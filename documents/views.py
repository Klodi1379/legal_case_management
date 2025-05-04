# documents/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator
from .models import Document, DocumentTemplate
from .forms import DocumentForm, DocumentTemplateForm
from cases.models import Case
import os

@login_required
def document_upload(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            messages.success(request, 'Document uploaded successfully.')
            return redirect('documents:recent_documents')
    else:
        form = DocumentForm()
    return render(request, 'documents/document_form.html', {'form': form})

@login_required
def document_list(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    documents = case.documents.all()
    return render(request, 'documents/document_list.html', {'case': case, 'documents': documents})

@login_required
def recent_documents(request):
    documents = Document.objects.all().order_by('-uploaded_at')[:10]
    return render(request, 'documents/recent_documents.html', {'documents': documents})

@login_required
def document_delete(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    if request.method == 'POST':
        document.delete()
        messages.success(request, 'Document deleted successfully.')
        return redirect('documents:recent_documents')
    return render(request, 'documents/document_confirm_delete.html', {'document': document})

# Document Template Views
@login_required
def template_upload(request):
    """View for uploading a new document template."""
    if request.method == 'POST':
        form = DocumentTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            messages.success(request, 'Document template uploaded successfully.')
            return redirect('documents:template_list')
    else:
        form = DocumentTemplateForm()

    return render(request, 'documents/template_form.html', {
        'form': form,
        'title': 'Upload Document Template'
    })

@login_required
def template_list(request):
    """View for listing all document templates."""
    templates = DocumentTemplate.objects.filter(is_active=True).order_by('-created_at')

    # Filter by document type if specified
    doc_type = request.GET.get('type')
    if doc_type:
        templates = templates.filter(document_type=doc_type)

    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        templates = templates.filter(name__icontains=search_query) | templates.filter(description__icontains=search_query)

    # Process file extensions for icons
    for template in templates:
        if template.file:
            ext = os.path.splitext(template.file.name)[1].lower()
            if ext in ['.doc', '.docx']:
                template.icon_class = 'fa-file-word'
            elif ext == '.pdf':
                template.icon_class = 'fa-file-pdf'
            elif ext == '.txt':
                template.icon_class = 'fa-file-alt'
            else:
                template.icon_class = 'fa-file'
        else:
            template.icon_class = 'fa-file'

    # Pagination
    paginator = Paginator(templates, 10)  # Show 10 templates per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get unique document types for filtering
    document_types = DocumentTemplate.objects.filter(is_active=True).values_list('document_type', flat=True).distinct()

    return render(request, 'documents/template_list.html', {
        'page_obj': page_obj,
        'document_types': document_types,
        'current_type': doc_type,
        'search_query': search_query
    })

@login_required
def template_detail(request, template_id):
    """View for viewing details of a document template."""
    template = get_object_or_404(DocumentTemplate, id=template_id)

    # Get file extension to determine appropriate icon
    if template.file:
        file_ext = os.path.splitext(template.file.name)[1].lower()
        if file_ext in ['.doc', '.docx']:
            template.icon_class = 'fa-file-word'
        elif file_ext == '.pdf':
            template.icon_class = 'fa-file-pdf'
        elif file_ext == '.txt':
            template.icon_class = 'fa-file-alt'
        else:
            template.icon_class = 'fa-file'

        # Get filename
        template.filename = template.file.name.split('/')[-1]
    else:
        file_ext = ''
        template.icon_class = 'fa-file'
        template.filename = 'No file attached'

    return render(request, 'documents/template_detail.html', {
        'template': template,
        'file_ext': file_ext
    })

@login_required
def template_delete(request, template_id):
    """View for deleting a document template."""
    template = get_object_or_404(DocumentTemplate, id=template_id)

    # Check if user has permission to delete
    if request.user != template.created_by and not request.user.is_staff:
        messages.error(request, "You don't have permission to delete this template.")
        return redirect('documents:template_list')

    if request.method == 'POST':
        template.delete()
        messages.success(request, 'Document template deleted successfully.')
        return redirect('documents:template_list')

    return render(request, 'documents/template_confirm_delete.html', {
        'template': template
    })

@login_required
def template_download(request, template_id):
    """View for downloading a document template."""
    template = get_object_or_404(DocumentTemplate, id=template_id)

    # Open the file and create a response with the file content
    response = HttpResponse(template.file, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{template.file.name.split("/")[-1]}"'

    return response