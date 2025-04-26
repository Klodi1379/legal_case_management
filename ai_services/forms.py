# ai_services/forms.py
from django import forms
from .models import LLMModel, PromptTemplate, VectorStore

class DocumentAnalysisForm(forms.Form):
    """Form for document analysis."""
    ANALYSIS_TYPE_CHOICES = (
        ('summary', 'Document Summary'),
        ('key_points', 'Extract Key Points'),
        ('legal_analysis', 'Legal Analysis'),
        ('precedent_search', 'Find Relevant Precedents'),
    )

    analysis_type = forms.ChoiceField(
        choices=ANALYSIS_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    model = forms.ModelChoiceField(
        queryset=LLMModel.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    custom_instructions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add any specific instructions for the analysis...'
        })
    )

class LegalResearchForm(forms.Form):
    """Form for legal research."""
    query = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter your legal research question...'
        })
    )

    case = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from cases.models import Case
        self.fields['case'].widget.choices = [(None, '-- Select Case (Optional) --')] + [
            (case.id, case.title) for case in Case.objects.all()
        ]

class DocumentGenerationForm(forms.Form):
    """Form for document generation."""
    DOCUMENT_TYPE_CHOICES = (
        ('letter', 'Letter'),
        ('pleading', 'Pleading'),
        ('contract', 'Contract'),
        ('memo', 'Legal Memorandum'),
        ('motion', 'Motion'),
        ('brief', 'Brief'),
        ('other', 'Other'),
    )

    document_type = forms.ChoiceField(
        choices=DOCUMENT_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    case = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Describe the content you want in the document...'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from cases.models import Case
        self.fields['case'].widget.choices = [(None, '-- Select Case (Optional) --')] + [
            (case.id, case.title) for case in Case.objects.all()
        ]

class SemanticSearchForm(forms.Form):
    """Form for semantic search."""
    query = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search documents...'
        })
    )

    case = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    limit = forms.IntegerField(
        required=False,
        initial=10,
        min_value=1,
        max_value=100,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        from cases.models import Case

        # If user is provided, filter cases by user
        if user:
            cases = Case.objects.filter(team_members__user=user).distinct()
        else:
            cases = Case.objects.all()

        self.fields['case'].widget.choices = [(None, '-- All Cases --')] + [
            (case.id, case.title) for case in cases
        ]

class LLMModelForm(forms.ModelForm):
    """Form for LLM model configuration."""
    class Meta:
        model = LLMModel
        fields = ['name', 'model_type', 'model_version', 'deployment_type',
                  'endpoint_url', 'max_tokens', 'temperature', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'model_type': forms.Select(attrs={'class': 'form-select'}),
            'model_version': forms.TextInput(attrs={'class': 'form-control'}),
            'deployment_type': forms.Select(attrs={'class': 'form-select'}),
            'endpoint_url': forms.URLInput(attrs={'class': 'form-control'}),
            'max_tokens': forms.NumberInput(attrs={'class': 'form-control'}),
            'temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PromptTemplateForm(forms.ModelForm):
    """Form for prompt template configuration."""
    class Meta:
        model = PromptTemplate
        fields = ['name', 'task_type', 'prompt_template', 'system_prompt',
                  'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'task_type': forms.Select(attrs={'class': 'form-select'}),
            'prompt_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'system_prompt': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class VectorStoreForm(forms.ModelForm):
    """Form for vector store configuration."""
    class Meta:
        model = VectorStore
        fields = ['name', 'store_type', 'connection_string', 'embedding_model',
                  'dimensions', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'store_type': forms.Select(attrs={'class': 'form-select'}),
            'connection_string': forms.TextInput(attrs={'class': 'form-control'}),
            'embedding_model': forms.TextInput(attrs={'class': 'form-control'}),
            'dimensions': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
