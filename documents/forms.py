# documents/forms.py
from django import forms
from .models import Document

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
