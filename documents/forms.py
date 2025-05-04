# documents/forms.py
from django import forms
from .models import Document, DocumentTemplate

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'file', 'description', 'document_type', 'case']

        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['document_type'].widget = forms.Select(choices=[
            ('', 'Select document type'),
            ('CONTRACT', 'Contract'),
            ('PLEADING', 'Pleading'),
            ('CORRESPONDENCE', 'Correspondence'),
            ('EVIDENCE', 'Evidence'),
            ('OTHER', 'Other'),
        ])

    def save(self, commit=True, user=None):
        document = super().save(commit=False)
        if user:
            document.uploaded_by = user
        if commit:
            document.save()
        return document

class DocumentTemplateForm(forms.ModelForm):
    class Meta:
        model = DocumentTemplate
        fields = ['name', 'description', 'file', 'document_type']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter template name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter template description'
            }),
            'document_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use a subset of document types that are most relevant for templates
        self.fields['document_type'].widget = forms.Select(attrs={'class': 'form-select'}, choices=[
            ('', 'Select document type'),
            ('PLEADING', 'Pleading'),
            ('MOTION', 'Motion'),
            ('BRIEF', 'Brief'),
            ('CONTRACT', 'Contract'),
            ('AGREEMENT', 'Agreement'),
            ('FORM', 'Form'),
            ('MEMO', 'Memo'),
            ('CORRESPONDENCE', 'Correspondence'),
            ('OTHER', 'Other'),
        ])

    def save(self, commit=True, user=None):
        template = super().save(commit=False)
        if user:
            template.created_by = user
        if commit:
            template.save()
        return template
