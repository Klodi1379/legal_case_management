"""
Admin configuration for AI services.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    LLMModel, PromptTemplate, VectorStore, 
    AIAnalysisRequest, AIAnalysisResult, DocumentEmbedding,
    AIGeneratedDocument, AISettings
)


@admin.register(LLMModel)
class LLMModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_type', 'model_version', 'deployment_type', 
                    'is_active', 'is_free', 'cost_display', 'api_key_status')
    list_filter = ('model_type', 'deployment_type', 'is_active', 'is_free')
    search_fields = ('name', 'model_version', 'endpoint_url')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'model_type', 'model_version', 'deployment_type', 'is_active', 'is_free')
        }),
        ('API Configuration', {
            'fields': ('endpoint_url', 'api_key', 'api_key_name', 'organization_id')
        }),
        ('Model Parameters', {
            'fields': ('max_tokens', 'temperature', 'top_p', 'frequency_penalty', 'presence_penalty', 'quantization')
        }),
        ('Cost Information', {
            'fields': ('cost_per_1k_tokens',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def cost_display(self, obj):
        if obj.is_free:
            return format_html('<span style="color: green;">FREE</span>')
        elif obj.cost_per_1k_tokens:
            return f"${obj.cost_per_1k_tokens}/1K"
        else:
            return "Not specified"
    cost_display.short_description = "Cost"
    
    def api_key_status(self, obj):
        if obj.api_key:
            return format_html('<span style="color: green;">✓ Configured</span>')
        else:
            return format_html('<span style="color: red;">✗ Not configured</span>')
    api_key_status.short_description = "API Key"


@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'task_type', 'created_by', 'is_active', 'created_at')
    list_filter = ('task_type', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'prompt_template')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('suitable_models',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'task_type', 'description', 'is_active')
        }),
        ('Prompt Content', {
            'fields': ('prompt_template', 'system_prompt')
        }),
        ('Model Configuration', {
            'fields': ('suitable_models',),
            'description': 'Select models that work well with this template.'
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(VectorStore)
class VectorStoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'store_type', 'dimensions', 'is_active', 'created_at')
    list_filter = ('store_type', 'is_active')
    search_fields = ('name', 'connection_string', 'embedding_model')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AIAnalysisRequest)
class AIAnalysisRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'analysis_type', 'status', 'llm_model', 'requested_by', 'created_at')
    list_filter = ('status', 'analysis_type', 'created_at')
    search_fields = ('id', 'input_text', 'combined_prompt')
    readonly_fields = ('created_at', 'completed_at')
    raw_id_fields = ('document', 'case', 'requested_by', 'llm_model', 'prompt_template')


@admin.register(AIAnalysisResult)
class AIAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('analysis_request', 'has_error', 'tokens_used', 'processing_time', 'created_at')
    list_filter = ('has_error', 'created_at')
    search_fields = ('output_text', 'error_message')
    readonly_fields = ('created_at',)
    raw_id_fields = ('analysis_request',)


@admin.register(DocumentEmbedding)
class DocumentEmbeddingAdmin(admin.ModelAdmin):
    list_display = ('document', 'vector_store', 'embedding_model', 'created_at')
    list_filter = ('vector_store', 'embedding_model', 'created_at')
    search_fields = ('document__title', 'vector_id')
    readonly_fields = ('created_at', 'last_updated')
    raw_id_fields = ('document', 'vector_store')


@admin.register(AIGeneratedDocument)
class AIGeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'case', 'is_approved', 'created_by', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('title',)
    readonly_fields = ('created_at',)
    raw_id_fields = ('analysis_result', 'document', 'case', 'created_by', 'approved_by')


@admin.register(AISettings)
class AISettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'is_public', 'updated_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('key', 'value', 'description')
    readonly_fields = ('created_at', 'updated_at')
