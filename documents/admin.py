from django.contrib import admin
from .models import (
    Document, DocumentCategory, DocumentTag,
    DocumentTagged, DocumentTemplate, SensitiveDocument
)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Document model."""
    list_display = ('title', 'document_type', 'case', 'uploaded_by', 'uploaded_at', 'version')
    list_filter = ('document_type', 'status', 'is_private', 'is_template')
    search_fields = ('title', 'description')
    readonly_fields = ('file_size', 'file_type', 'uploaded_at', 'modified_at')
    date_hierarchy = 'uploaded_at'

@admin.register(SensitiveDocument)
class SensitiveDocumentAdmin(admin.ModelAdmin):
    """Admin interface for SensitiveDocument model."""
    list_display = ('title', 'document_type', 'sensitivity_level', 'case', 'uploaded_by', 'uploaded_at')
    list_filter = ('document_type', 'sensitivity_level')
    search_fields = ('title', 'description')
    readonly_fields = ('file_size', 'file_type', 'uploaded_at', 'modified_at', 'encryption_salt')
    date_hierarchy = 'uploaded_at'

    def get_queryset(self, request):
        """Only show sensitive documents to staff with appropriate permissions."""
        qs = super().get_queryset(request)
        if not request.user.has_perm('documents.view_any_sensitive_document'):
            qs = qs.filter(authorized_users=request.user)
        return qs

@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    """Admin interface for DocumentCategory model."""
    list_display = ('name', 'parent')
    search_fields = ('name', 'description')

@admin.register(DocumentTag)
class DocumentTagAdmin(admin.ModelAdmin):
    """Admin interface for DocumentTag model."""
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    """Admin interface for DocumentTemplate model."""
    list_display = ('name', 'document_type', 'created_by', 'created_at', 'is_active')
    list_filter = ('document_type', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
