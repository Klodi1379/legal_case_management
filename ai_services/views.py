from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import logging
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
import json

logger = logging.getLogger(__name__)

from .models import LLMModel, PromptTemplate, AIAnalysisRequest, AIAnalysisResult, VectorStore, DocumentEmbedding
from documents.models import Document
from cases.models import Case
from .forms import (
    DocumentAnalysisForm, LegalResearchForm,
    DocumentGenerationForm, SemanticSearchForm,
    LLMModelForm, PromptTemplateForm, VectorStoreForm
)
from .services.prompt_manager import PromptManager
# Use service factory to get appropriate services
from .services.service_factory import AIServiceFactory
from .tasks import process_analysis_request, create_document_embeddings

# Dashboard view
@login_required
def ai_dashboard(request):
    """Dashboard for AI services."""
    # Get statistics
    total_analyses = AIAnalysisRequest.objects.count()
    completed_analyses = AIAnalysisRequest.objects.filter(status='COMPLETED').count()
    failed_analyses = AIAnalysisRequest.objects.filter(status='FAILED').count()

    # Get recent analyses
    recent_analyses = AIAnalysisRequest.objects.select_related(
        'document', 'llm_model', 'requested_by'
    ).order_by('-created_at')[:5]

    # Get active models
    active_models = LLMModel.objects.filter(is_active=True)

    # Get analysis by type
    analysis_by_type = AIAnalysisRequest.objects.values('analysis_type').annotate(
        count=Count('id')
    ).order_by('-count')

    # Get vector stores and document embeddings
    vector_stores = VectorStore.objects.all()
    document_embeddings = DocumentEmbedding.objects.all()

    # Get prompt templates
    prompt_templates = PromptTemplate.objects.all()

    context = {
        'total_analyses': total_analyses,
        'completed_analyses': completed_analyses,
        'failed_analyses': failed_analyses,
        'recent_analyses': recent_analyses,
        'active_models': active_models,
        'analysis_by_type': analysis_by_type,
        'vector_stores': vector_stores,
        'document_embeddings': document_embeddings,
        'prompt_templates': prompt_templates,
        'now': timezone.now(),
    }

    return render(request, 'ai_services/dashboard.html', context)

# Semantic Search views
@login_required
def semantic_search(request):
    """View for semantic search of documents."""
    results = []

    # Get cases for the form
    cases = Case.objects.all()

    if request.method == 'GET' and 'query' in request.GET:
        form = SemanticSearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            case = form.cleaned_data.get('case')
            limit = form.cleaned_data.get('limit', 10)

            # Get default vector store
            vector_store = VectorStore.objects.filter(is_active=True).first()
            if vector_store:
                # Use service factory to get appropriate search service
                search_service = AIServiceFactory.get_vector_search_service(vector_store)
                results = search_service.search(
                    query=query,
                    limit=limit,
                    case_id=case.id if case else None
                )
    else:
        form = SemanticSearchForm()

    context = {
        'form': form,
        'results': results,
        'cases': cases,
    }

    return render(request, 'ai_services/semantic_search.html', context)

@login_required
@require_POST
def submit_semantic_search(request):
    """Submit a semantic search query."""
    if request.method == 'POST':
        form = SemanticSearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            case_id = form.cleaned_data.get('case')
            limit = form.cleaned_data.get('limit', 10)

            # Redirect to search results
            url = f'/ai/semantic-search/?query={query}'
            if case_id:
                url += f'&case={case_id}'
            if limit:
                url += f'&limit={limit}'

            return redirect(url)

    # If form is invalid, redirect back to search page
    messages.error(request, "Invalid search query.")
    return redirect('ai_services:semantic_search')

# Document Analysis Views
@login_required
def document_analysis(request, document_id):
    """View for analyzing a document with AI."""
    from documents.models import Document
    document = get_object_or_404(Document, id=document_id)

    # Check permissions
    if not request.user.has_perm('documents.view_document') or \
       (document.is_private and document.uploaded_by != request.user):
        messages.error(request, "You don't have permission to analyze this document.")
        return redirect('documents:document_list')

    # Get available models
    models = LLMModel.objects.filter(is_active=True)

    # Get previous analyses
    previous_analyses = AIAnalysisRequest.objects.filter(
        document=document
    ).select_related('result').order_by('-created_at')

    context = {
        'document': document,
        'models': models,
        'previous_analyses': previous_analyses,
    }

    return render(request, 'ai_services/document_analysis.html', context)

@login_required
@require_POST
def submit_analysis(request, document_id):
    """Submit a document for AI analysis."""
    from documents.models import Document
    document = get_object_or_404(Document, id=document_id)

    # Check permissions
    if not request.user.has_perm('documents.view_document'):
        messages.error(request, "You don't have permission to analyze this document.")
        return redirect('documents:document_list')

    # Get form data
    analysis_type = request.POST.get('analysis_type')
    model_id = request.POST.get('model_id')
    custom_instructions = request.POST.get('custom_instructions', '')

    try:
        # Get model
        model = LLMModel.objects.get(id=model_id)

        # Get appropriate prompt template
        prompt_template = PromptTemplate.objects.filter(
            task_type=analysis_type,
            is_active=True
        ).first()

        if not prompt_template:
            messages.error(request, f"No active prompt template found for {analysis_type}.")
            return redirect('ai_services:document_analysis', document_id=document_id)

        # Build prompt
        prompt_manager = PromptManager()
        prompt = prompt_manager.build_document_analysis_prompt(
            template=prompt_template,
            document=document,
            custom_instructions=custom_instructions
        )

        # Create analysis request
        analysis_request = AIAnalysisRequest.objects.create(
            analysis_type=analysis_type,
            llm_model=model,
            document=document,
            custom_instructions=custom_instructions,
            combined_prompt=prompt,
            status='PENDING',
            requested_by=request.user,
            created_at=timezone.now()
        )

        # Process asynchronously
        # In a real implementation, this would be a Celery task
        try:
            # Get appropriate service
            llm_service = AIServiceFactory.get_llm_service(model)

            # Update status
            analysis_request.status = 'PROCESSING'
            analysis_request.save()

            # Process request
            result = llm_service.generate_text(prompt=prompt)

            # Save result
            AIAnalysisResult.objects.create(
                request=analysis_request,
                output_text=result['text'],
                raw_response=result,
                tokens_used=result.get('tokens_used', 0),
                processing_time=result.get('processing_time', 0),
                created_at=timezone.now()
            )

            # Update request status
            analysis_request.status = 'COMPLETED'
            analysis_request.completed_at = timezone.now()
            analysis_request.save()

        except Exception as e:
            logger.error(f"Error processing analysis request: {str(e)}")
            analysis_request.status = 'FAILED'
            analysis_request.save()

            # Create result with error
            AIAnalysisResult.objects.create(
                analysis_request=analysis_request,
                output_text="Error processing request",
                raw_response={"error": str(e)},
                has_error=True,
                error_message=str(e),
                created_at=timezone.now()
            )

        messages.success(request, "Analysis request submitted successfully.")
        return redirect('ai_services:analysis_result', analysis_id=analysis_request.id)

    except Exception as e:
        logger.error(f"Error submitting analysis request: {str(e)}")
        messages.error(request, f"Error submitting analysis request: {str(e)}")
        return redirect('ai_services:document_analysis', document_id=document_id)

@login_required
def analysis_result(request, analysis_id):
    """View the result of a document analysis."""
    analysis = get_object_or_404(
        AIAnalysisRequest.objects.select_related('result', 'document', 'llm_model', 'requested_by'),
        id=analysis_id
    )

    # Check permissions
    if not request.user.has_perm('ai_services.view_aianalysisrequest') and \
       analysis.requested_by != request.user:
        messages.error(request, "You don't have permission to view this analysis.")
        return redirect('documents:document_list')

    # For key points analysis, parse the result into a list
    key_points = []
    if analysis.status == 'COMPLETED' and analysis.analysis_type == 'KEY_POINTS' and hasattr(analysis, 'result'):
        # Simple parsing - in a real implementation, this would be more sophisticated
        key_points = [point.strip() for point in analysis.result.output_text.split('\n') if point.strip()]

    context = {
        'analysis': analysis,
        'key_points': key_points,
    }

    return render(request, 'ai_services/analysis_result.html', context)

@login_required
def legal_research(request):
    """View for legal research with AI."""
    results = None
    cases = Case.objects.all()
    models = LLMModel.objects.filter(is_active=True)

    form = LegalResearchForm()

    context = {
        'form': form,
        'results': results,
        'cases': cases,
        'models': models,
    }

    return render(request, 'ai_services/legal_research.html', context)

@login_required
@require_POST
def submit_research(request):
    """Submit a legal research query."""
    results = None

    if request.method == 'POST':
        form = LegalResearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            case_id = form.cleaned_data.get('case')
            model_id = request.POST.get('model_id')

            try:
                # Get model
                model = LLMModel.objects.get(id=model_id)

                # Get appropriate service
                llm_service = AIServiceFactory.get_llm_service(model)

                # Get appropriate prompt template
                prompt_template = PromptTemplate.objects.filter(
                    task_type='legal_research',
                    is_active=True
                ).first()

                if prompt_template:
                    # Build prompt
                    prompt_manager = PromptManager()
                    prompt = prompt_manager.format_prompt(
                        template=prompt_template,
                        context={
                            'query': query,
                            'case_id': case_id,
                        }
                    )

                    # Create analysis request
                    analysis_request = AIAnalysisRequest.objects.create(
                        analysis_type='LEGAL_RESEARCH',
                        llm_model=model,
                        prompt_template=prompt_template,
                        case_id=case_id,
                        combined_prompt=prompt,
                        input_text=query,
                        status='PENDING',
                        requested_by=request.user,
                        created_at=timezone.now()
                    )

                    # Process request
                    try:
                        # Update status
                        analysis_request.status = 'PROCESSING'
                        analysis_request.save()

                        # Generate response
                        result = llm_service.generate_text(prompt=prompt)

                        # Save result
                        AIAnalysisResult.objects.create(
                            analysis_request=analysis_request,
                            output_text=result['text'],
                            raw_response=result,
                            tokens_used=result.get('tokens_used', 0),
                            processing_time=result.get('processing_time', 0),
                            created_at=timezone.now()
                        )

                        # Update request status
                        analysis_request.status = 'COMPLETED'
                        analysis_request.completed_at = timezone.now()
                        analysis_request.save()

                        messages.success(request, "Research completed successfully.")
                        return redirect('ai_services:analysis_result', analysis_id=analysis_request.id)

                    except Exception as e:
                        logger.error(f"Error processing research request: {str(e)}")
                        analysis_request.status = 'FAILED'
                        analysis_request.error_message = str(e)
                        analysis_request.save()
                        messages.error(request, f"Error processing research: {str(e)}")

            except Exception as e:
                logger.error(f"Error submitting research request: {str(e)}")
                messages.error(request, f"Error submitting research: {str(e)}")

    # If we get here, something went wrong
    return redirect('ai_services:legal_research')

@login_required
def document_generation(request):
    """View for document generation with AI."""
    cases = Case.objects.all()
    models = LLMModel.objects.filter(is_active=True)

    form = DocumentGenerationForm()

    context = {
        'form': form,
        'cases': cases,
        'models': models,
    }

    return render(request, 'ai_services/document_generation.html', context)

@login_required
@require_POST
def submit_document_generation(request):
    """Submit a document generation request."""
    if request.method == 'POST':
        form = DocumentGenerationForm(request.POST)
        if form.is_valid():
            document_type = form.cleaned_data['document_type']
            case_id = form.cleaned_data.get('case')
            content = form.cleaned_data['content']
            model_id = request.POST.get('model_id')

            try:
                # Get model
                model = LLMModel.objects.get(id=model_id)

                # Get case if provided
                case = None
                if case_id:
                    case = Case.objects.get(id=case_id)

                # Get appropriate service
                llm_service = AIServiceFactory.get_llm_service(model)

                # Get appropriate prompt template
                prompt_template = PromptTemplate.objects.filter(
                    task_type='document_generation',
                    is_active=True
                ).first()

                if prompt_template:
                    # Build prompt
                    prompt_manager = PromptManager()
                    prompt = prompt_manager.format_prompt(
                        template=prompt_template,
                        context={
                            'document_type': document_type,
                            'case_id': case_id,
                            'content': content,
                        }
                    )

                    # Create analysis request
                    analysis_request = AIAnalysisRequest.objects.create(
                        analysis_type='DOCUMENT_GENERATION',
                        llm_model=model,
                        prompt_template=prompt_template,
                        case=case,
                        combined_prompt=prompt,
                        input_text=content,
                        status='PENDING',
                        requested_by=request.user,
                        created_at=timezone.now()
                    )

                    # Process request
                    try:
                        # Update status
                        analysis_request.status = 'PROCESSING'
                        analysis_request.save()

                        # Generate document
                        result = llm_service.generate_text(prompt=prompt)

                        # Save result
                        AIAnalysisResult.objects.create(
                            analysis_request=analysis_request,
                            output_text=result['text'],
                            raw_response=result,
                            tokens_used=result.get('tokens_used', 0),
                            processing_time=result.get('processing_time', 0),
                            created_at=timezone.now()
                        )

                        # Update request status
                        analysis_request.status = 'COMPLETED'
                        analysis_request.completed_at = timezone.now()
                        analysis_request.save()

                        # Create a document from the generated text
                        document_title = f"{document_type} - {timezone.now().strftime('%Y-%m-%d')}"
                        if case:
                            document_title = f"{case.title} - {document_title}"

                        # Create the document
                        from documents.models import Document
                        document = Document.objects.create(
                            title=document_title,
                            content=result['text'],
                            document_type=document_type,
                            case=case,
                            uploaded_by=request.user,
                            is_generated=True
                        )

                        # Create AI generated document record
                        from .models import AIGeneratedDocument
                        AIGeneratedDocument.objects.create(
                            title=document_title,
                            analysis_result=analysis_request.result,
                            document=document,
                            created_by=request.user,
                            case=case
                        )

                        messages.success(request, "Document generated successfully.")
                        return redirect('documents:document_detail', document_id=document.id)

                    except Exception as e:
                        logger.error(f"Error processing document generation: {str(e)}")
                        analysis_request.status = 'FAILED'
                        analysis_request.error_message = str(e)
                        analysis_request.save()
                        messages.error(request, f"Error generating document: {str(e)}")

            except Exception as e:
                logger.error(f"Error submitting document generation: {str(e)}")
                messages.error(request, f"Error submitting document generation: {str(e)}")

    # If we get here, something went wrong
    return redirect('ai_services:document_generation')

# Model Management Views
@staff_member_required
def model_list(request):
    """List all LLM models."""
    models = LLMModel.objects.all().order_by('-is_active', 'name')

    context = {
        'models': models,
    }

    return render(request, 'ai_services/model_list.html', context)

@staff_member_required
def model_create(request):
    """Create a new LLM model."""
    if request.method == 'POST':
        form = LLMModelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Model created successfully.")
            return redirect('ai_services:model_list')
    else:
        form = LLMModelForm()

    context = {
        'form': form,
        'title': 'Create New Model',
    }

    return render(request, 'ai_services/model_form.html', context)

@staff_member_required
def model_edit(request, model_id):
    """Edit an existing LLM model."""
    model = get_object_or_404(LLMModel, id=model_id)

    if request.method == 'POST':
        form = LLMModelForm(request.POST, instance=model)
        if form.is_valid():
            form.save()
            messages.success(request, "Model updated successfully.")
            return redirect('ai_services:model_list')
    else:
        form = LLMModelForm(instance=model)

    context = {
        'form': form,
        'title': f'Edit Model: {model.name}',
        'model': model,
    }

    return render(request, 'ai_services/model_form.html', context)

@staff_member_required
def model_delete(request, model_id):
    """Delete an LLM model."""
    model = get_object_or_404(LLMModel, id=model_id)

    if request.method == 'POST':
        model.delete()
        messages.success(request, "Model deleted successfully.")
        return redirect('ai_services:model_list')

    context = {
        'model': model,
    }

    return render(request, 'ai_services/model_confirm_delete.html', context)

# Prompt Template Management Views
@staff_member_required
def prompt_list(request):
    """List all prompt templates."""
    prompts = PromptTemplate.objects.all().order_by('-is_active', 'name')

    context = {
        'prompts': prompts,
    }

    return render(request, 'ai_services/prompt_list.html', context)

@staff_member_required
def prompt_create(request):
    """Create a new prompt template."""
    if request.method == 'POST':
        form = PromptTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Prompt template created successfully.")
            return redirect('ai_services:prompt_list')
    else:
        form = PromptTemplateForm()

    context = {
        'form': form,
        'title': 'Create New Prompt Template',
    }

    return render(request, 'ai_services/prompt_form.html', context)

@staff_member_required
def prompt_edit(request, prompt_id):
    """Edit an existing prompt template."""
    prompt = get_object_or_404(PromptTemplate, id=prompt_id)

    if request.method == 'POST':
        form = PromptTemplateForm(request.POST, instance=prompt)
        if form.is_valid():
            form.save()
            messages.success(request, "Prompt template updated successfully.")
            return redirect('ai_services:prompt_list')
    else:
        form = PromptTemplateForm(instance=prompt)

    context = {
        'form': form,
        'title': f'Edit Prompt Template: {prompt.name}',
        'prompt': prompt,
    }

    return render(request, 'ai_services/prompt_form.html', context)

@staff_member_required
def prompt_delete(request, prompt_id):
    """Delete a prompt template."""
    prompt = get_object_or_404(PromptTemplate, id=prompt_id)

    if request.method == 'POST':
        prompt.delete()
        messages.success(request, "Prompt template deleted successfully.")
        return redirect('ai_services:prompt_list')

    context = {
        'prompt': prompt,
    }

    return render(request, 'ai_services/prompt_confirm_delete.html', context)

# Vector Store Management Views
@staff_member_required
def vector_store_list(request):
    """List all vector stores."""
    stores = VectorStore.objects.all().order_by('-is_active', 'name')

    context = {
        'stores': stores,
    }

    return render(request, 'ai_services/vector_store_list.html', context)

@staff_member_required
def vector_store_create(request):
    """Create a new vector store."""
    if request.method == 'POST':
        form = VectorStoreForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Vector store created successfully.")
            return redirect('ai_services:vector_store_list')
    else:
        form = VectorStoreForm()

    context = {
        'form': form,
        'title': 'Create New Vector Store',
    }

    return render(request, 'ai_services/vector_store_form.html', context)

@staff_member_required
def vector_store_edit(request, store_id):
    """Edit an existing vector store."""
    store = get_object_or_404(VectorStore, id=store_id)

    if request.method == 'POST':
        form = VectorStoreForm(request.POST, instance=store)
        if form.is_valid():
            form.save()
            messages.success(request, "Vector store updated successfully.")
            return redirect('ai_services:vector_store_list')
    else:
        form = VectorStoreForm(instance=store)

    context = {
        'form': form,
        'title': f'Edit Vector Store: {store.name}',
        'store': store,
    }

    return render(request, 'ai_services/vector_store_form.html', context)

@staff_member_required
def vector_store_delete(request, store_id):
    """Delete a vector store."""
    store = get_object_or_404(VectorStore, id=store_id)

    if request.method == 'POST':
        store.delete()
        messages.success(request, "Vector store deleted successfully.")
        return redirect('ai_services:vector_store_list')

    context = {
        'store': store,
    }

    return render(request, 'ai_services/vector_store_confirm_delete.html', context)
