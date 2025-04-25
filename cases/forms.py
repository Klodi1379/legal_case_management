# cases/forms.py
from django import forms
from .models import Case, CaseNote

class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = ['title', 'case_number', 'client', 'status', 'case_type', 'description']

class CaseNoteForm(forms.ModelForm):
    class Meta:
        model = CaseNote
        fields = ['content']