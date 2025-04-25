"""
Models for AI services.

This module defines the database models for AI services, including
LLM models, vector stores, and analysis requests.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class LLMModel(models.Model):
    """
    Configuration for an LLM model.
    """
    name = models.CharField(_("Model Name"), max_length=100)
    endpoint_url = models.URLField(_("Endpoint URL"), max_length=255)
    api_key = models.CharField(_("API Key"), max_length=255, blank=True, null=True)
    max_tokens = models.IntegerField(_("Max Tokens"), default=4096)
    temperature = models.FloatField(_("Temperature"), default=0.7)
    is_active = models.BooleanField(_("Is Active"), default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _("LLM Model")
        verbose_name_plural = _("LLM Models")


class VectorStore(models.Model):
    """
    Configuration for a vector store.
    """
    name = models.CharField(_("Store Name"), max_length=100)
    store_type = models.CharField(_("Store Type"), max_length=50, choices=[
        ('chroma', 'ChromaDB'),
        ('pinecone', 'Pinecone'),
        ('mock', 'Mock Store'),
    ], default='chroma')
    connection_string = models.CharField(_("Connection String"), max_length=255, blank=True, null=True)
    dimensions = models.IntegerField(_("Dimensions"), default=768)
    embedding_model = models.CharField(_("Embedding Model"), max_length=100, default="gemma-3-12b-it-qat")
    is_active = models.BooleanField(_("Is Active"), default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _("Vector Store")
        verbose_name_plural = _("Vector Stores")


class AnalysisRequest(models.Model):
    """
    A request for document analysis.
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='analysis_requests')
    document = models.ForeignKey('documents.Document', on_delete=models.CASCADE, related_name='analysis_requests')
    request_type = models.CharField(_("Request Type"), max_length=50, choices=[
        ('summary', _('Summary')),
        ('key_points', _('Key Points')),
        ('legal_analysis', _('Legal Analysis')),
        ('precedent_search', _('Precedent Search')),
    ])
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    completed_at = models.DateTimeField(_("Completed At"), null=True, blank=True)
    result = models.TextField(_("Result"), blank=True, null=True)
    error_message = models.TextField(_("Error Message"), blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_request_type_display()} for {self.document}"
    
    class Meta:
        verbose_name = _("Analysis Request")
        verbose_name_plural = _("Analysis Requests")
        ordering = ['-created_at']
