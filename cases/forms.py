# cases/forms.py
from django import forms
from .models import Case, CaseNote, ConflictCheck, CaseEvent

class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = ['title', 'case_number', 'client', 'status', 'case_type', 'description', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class CaseNoteForm(forms.ModelForm):
    class Meta:
        model = CaseNote
        fields = ['title', 'content', 'is_private']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }

class ConflictCheckForm(forms.ModelForm):
    """Form for creating and updating conflict checks."""

    class Meta:
        model = ConflictCheck
        fields = ['check_source', 'parties_checked', 'resolution_status', 'resolution_notes']
        widgets = {
            'parties_checked': forms.HiddenInput(),
            'resolution_notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make resolution fields not required for initial creation
        self.fields['resolution_status'].required = False
        self.fields['resolution_notes'].required = False

        # If this is an existing check with conflicts, require resolution
        if self.instance.pk and self.instance.conflicts_found:
            self.fields['resolution_status'].required = True

class CaseEventForm(forms.ModelForm):
    """Form for creating and updating case events."""

    class Meta:
        model = CaseEvent
        fields = ['title', 'event_type', 'description', 'date', 'time', 'location', 'is_critical']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }