"""
Models for AI services.

This module defines the database models for AI services, including
LLM models, vector stores, and analysis requests.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class LLMModel(models.Model):
    """
    Configuration for an LLM model.
    """
    MODEL_TYPE_CHOICES = (
        ('gemma_3', 'Gemma 3'),
        ('gemma_2', 'Gemma 2'),
        ('llama_3', 'Llama 3'),
        ('mistral', 'Mistral'),
        ('other', 'Other Open Source Model'),
    )
    DEPLOYMENT_TYPE_CHOICES = (
        ('local', 'Local Deployment'),
        ('containerized', 'Containerized'),
        ('api', 'API Service'),
        ('vllm', 'vLLM Deployment'),
    )

    name = models.CharField(_("Model Name"), max_length=100)
    model_type = models.CharField(_("Model Type"), max_length=20, choices=MODEL_TYPE_CHOICES, default='gemma_3')
    model_version = models.CharField(_("Model Version"), max_length=50, default='3-12b-it-qat')
    deployment_type = models.CharField(_("Deployment Type"), max_length=20, choices=DEPLOYMENT_TYPE_CHOICES, default='api')
    endpoint_url = models.URLField(_("Endpoint URL"), max_length=255)
    api_key = models.CharField(_("API Key"), max_length=255, blank=True, null=True)
    max_tokens = models.IntegerField(_("Max Tokens"), default=4096)
    temperature = models.FloatField(_("Temperature"), default=0.7)
    quantization = models.CharField(_("Quantization"), max_length=20, blank=True, help_text=_("Model quantization (e.g., 4bit, 8bit)"))
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.model_type}-{self.model_version})"

    class Meta:
        verbose_name = _("LLM Model")
        verbose_name_plural = _("LLM Models")
        ordering = ['-is_active', 'name']

class PromptTemplate(models.Model):
    """
    Templates for LLM prompts by task type.
    """
    TASK_TYPE_CHOICES = (
        ('document_summarization', 'Document Summarization'),
        ('key_points', 'Extract Key Points'),
        ('legal_analysis', 'Legal Analysis'),
        ('precedent_search', 'Find Relevant Precedents'),
        ('legal_research', 'Legal Research'),
        ('document_generation', 'Document Generation'),
        ('contract_analysis', 'Contract Analysis'),
        ('client_intake', 'Client Intake Processing'),
        ('custom', 'Custom Task'),
    )

    name = models.CharField(_("Template Name"), max_length=100)
    task_type = models.CharField(_("Task Type"), max_length=30, choices=TASK_TYPE_CHOICES)
    prompt_template = models.TextField(_("Prompt Template"))
    system_prompt = models.TextField(_("System Prompt"), blank=True, help_text=_("System prompt for models that support it"))
    description = models.TextField(_("Description"), blank=True)
    suitable_models = models.ManyToManyField(LLMModel, related_name='suitable_prompts', blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_prompts')
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    is_active = models.BooleanField(_("Is Active"), default=True)

    def __str__(self):
        return f"{self.name} ({self.task_type})"

    class Meta:
        verbose_name = _("Prompt Template")
        verbose_name_plural = _("Prompt Templates")


class VectorStore(models.Model):
    """
    Configuration for a vector store.
    """
    STORE_TYPE_CHOICES = [
        ('pgvector', 'PostgreSQL pgvector'),
        ('chroma', 'ChromaDB'),
        ('pinecone', 'Pinecone'),
        ('qdrant', 'Qdrant'),
        ('mock', 'Mock Store'),
    ]

    name = models.CharField(_("Store Name"), max_length=100)
    store_type = models.CharField(_("Store Type"), max_length=50, choices=STORE_TYPE_CHOICES, default='pgvector')
    connection_string = models.CharField(_("Connection String"), max_length=255, blank=True, null=True)
    dimensions = models.IntegerField(_("Dimensions"), default=768)
    embedding_model = models.CharField(_("Embedding Model"), max_length=100, default="gemma-3-embedding")
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Vector Store")
        verbose_name_plural = _("Vector Stores")
        ordering = ['-is_active', 'name']


class AIAnalysisRequest(models.Model):
    """
    A request for AI analysis of a document or other content.
    """
    STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('PROCESSING', _('Processing')),
        ('COMPLETED', _('Completed')),
        ('FAILED', _('Failed')),
    ]

    ANALYSIS_TYPE_CHOICES = [
        ('DOCUMENT_SUMMARY', _('Document Summary')),
        ('KEY_POINTS', _('Key Points')),
        ('LEGAL_ANALYSIS', _('Legal Analysis')),
        ('PRECEDENT_SEARCH', _('Precedent Search')),
        ('CONTRACT_REVIEW', _('Contract Review')),
        ('LEGAL_RESEARCH', _('Legal Research')),
        ('DOCUMENT_GENERATION', _('Document Generation')),
        ('CUSTOM', _('Custom Analysis')),
    ]

    # Basic information
    analysis_type = models.CharField(_("Analysis Type"), max_length=50, choices=ANALYSIS_TYPE_CHOICES)
    llm_model = models.ForeignKey(LLMModel, on_delete=models.SET_NULL, null=True, related_name='analysis_requests', verbose_name=_("LLM Model"))
    prompt_template = models.ForeignKey(PromptTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='analysis_requests', verbose_name=_("Prompt Template"))

    # Related objects
    document = models.ForeignKey('documents.Document', on_delete=models.CASCADE, related_name='ai_analyses', null=True, blank=True, verbose_name=_("Document"))
    case = models.ForeignKey('cases.Case', on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_analyses', verbose_name=_("Case"))

    # Prompt information
    input_text = models.TextField(_("Input Text"), blank=True, help_text=_("Input text for analysis (if not using a document)"))
    combined_prompt = models.TextField(_("Combined Prompt"), help_text=_("The full prompt sent to the LLM"))
    custom_instructions = models.TextField(_("Custom Instructions"), blank=True)
    context_items = models.JSONField(_("Context Items"), default=list, blank=True, help_text=_("IDs of documents or other items used for context"))

    # Status information
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requested_analyses', verbose_name=_("Requested By"))
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # Timestamps
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    completed_at = models.DateTimeField(_("Completed At"), null=True, blank=True)

    def __str__(self):
        if self.document:
            return f"{self.get_analysis_type_display()} for {self.document}"
        return f"{self.get_analysis_type_display()} ({self.id})"

    def get_status_display_with_color(self):
        """Return status with appropriate color class for UI."""
        status_colors = {
            'PENDING': 'secondary',
            'PROCESSING': 'info',
            'COMPLETED': 'success',
            'FAILED': 'danger',
        }
        return {
            'status': self.get_status_display(),
            'color': status_colors.get(self.status, 'secondary')
        }

    class Meta:
        verbose_name = _("AI Analysis Request")
        verbose_name_plural = _("AI Analysis Requests")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['analysis_type', '-created_at']),
        ]

class AIAnalysisResult(models.Model):
    """
    Result of an AI analysis request.
    """
    analysis_request = models.OneToOneField(AIAnalysisRequest, on_delete=models.CASCADE, related_name='result', verbose_name=_("Analysis Request"))
    output_text = models.TextField(_("Output Text"))
    raw_response = models.JSONField(_("Raw Response"), default=dict)
    tokens_used = models.IntegerField(_("Tokens Used"), null=True, blank=True)
    processing_time = models.FloatField(_("Processing Time (seconds)"), null=True, blank=True)
    has_error = models.BooleanField(_("Has Error"), default=False)
    error_message = models.TextField(_("Error Message"), blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    def __str__(self):
        return f"Result for {self.analysis_request}"

    def get_truncated_output(self, max_length=200):
        """Get truncated output for display."""
        if len(self.output_text) <= max_length:
            return self.output_text
        return self.output_text[:max_length] + "..."

    class Meta:
        verbose_name = _("AI Analysis Result")
        verbose_name_plural = _("AI Analysis Results")
        ordering = ['-created_at']


class DocumentEmbedding(models.Model):
    """
    Vector embeddings for semantic search of documents.
    """
    document = models.OneToOneField('documents.Document', on_delete=models.CASCADE, related_name='embedding', verbose_name=_("Document"))
    vector_store = models.ForeignKey(VectorStore, on_delete=models.CASCADE, related_name='document_embeddings', verbose_name=_("Vector Store"))
    vector_id = models.CharField(_("Vector ID"), max_length=100, help_text=_("ID in the vector store"))
    embedding_model = models.CharField(_("Embedding Model"), max_length=100)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    last_updated = models.DateTimeField(_("Last Updated"), auto_now=True)

    def __str__(self):
        return f"Embedding for {self.document}"

    class Meta:
        verbose_name = _("Document Embedding")
        verbose_name_plural = _("Document Embeddings")
        ordering = ['-created_at']


class AIGeneratedDocument(models.Model):
    """
    Documents generated by AI.
    """
    title = models.CharField(_("Title"), max_length=255)
    analysis_result = models.ForeignKey(AIAnalysisResult, on_delete=models.SET_NULL, null=True, related_name='generated_documents', verbose_name=_("Analysis Result"))
    document = models.OneToOneField('documents.Document', on_delete=models.CASCADE, related_name='ai_source', verbose_name=_("Document"))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_generated_documents', verbose_name=_("Created By"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    case = models.ForeignKey('cases.Case', on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_generated_documents', verbose_name=_("Case"))
    is_approved = models.BooleanField(_("Approved"), default=False)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_ai_documents', verbose_name=_("Approved By"))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("AI Generated Document")
        verbose_name_plural = _("AI Generated Documents")
        ordering = ['-created_at']


class AISettings(models.Model):
    """
    Global settings for AI services.
    """
    key = models.CharField(_("Key"), max_length=100, unique=True)
    value = models.TextField(_("Value"))
    description = models.TextField(_("Description"), blank=True)
    is_public = models.BooleanField(_("Public"), default=False, help_text=_("Whether this setting is visible to non-admin users"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    def __str__(self):
        return self.key

    class Meta:
        verbose_name = _("AI Setting")
        verbose_name_plural = _("AI Settings")
        ordering = ['key']
