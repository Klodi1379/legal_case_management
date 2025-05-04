# portal/forms.py
from django import forms
from .models import Message, MessageThread, ClientTask

class MessageForm(forms.ModelForm):
    """
    Form for creating new messages in the client portal.
    """
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        }

class MessageThreadForm(forms.ModelForm):
    """
    Form for creating new message threads.
    """
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
                             label="Initial Message")
    
    class Meta:
        model = MessageThread
        fields = ['subject', 'case']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'case': forms.Select(attrs={'class': 'form-select'}),
        }

class ClientTaskForm(forms.ModelForm):
    """
    Form for client tasks.
    """
    class Meta:
        model = ClientTask
        fields = ['title', 'description', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
