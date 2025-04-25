from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import logging
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required

logger = logging.getLogger(__name__)

from .models import (
    LLMModel, PromptTemplate, AIAnalysisRequest,
    AIAnalysisResult, Document, VectorStore
)
from .forms import (
    DocumentAnalysisForm, LegalResearchForm,
    DocumentGenerationForm, SemanticSearchForm,
    LLMModelForm, PromptTemplateForm, VectorStoreForm
)
from .services.prompt_manager import PromptManager
# Use service factory to get appropriate services
from .services.service_factory import AIServiceFactory
from .tasks import process_analysis_request, create_document_embeddings

# Example of a view that uses the service factory
@login_required
def semantic_search_view(request):
    """View for semantic search of documents."""
    results = []

    # Get cases for the form
    from cases.models import Case
    cases = Case.objects.all()

    if request.method == 'GET' and 'query' in request.GET:
        form = SemanticSearchForm(request.GET, user=request.user)
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
        form = SemanticSearchForm(user=request.user)

    context = {
        'form': form,
        'results': results,
        'cases': cases,
    }

    return render(request, 'ai_services/semantic_search.html', context)

# Other views would be updated similarly to use the service factory
