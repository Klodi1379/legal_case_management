# documents/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Document
from .forms import DocumentForm
from cases.models import Case

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