from django.contrib import admin
from .models import AuditLog, SystemSetting

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog model."""
    list_display = ('user', 'action', 'content_type', 'object_repr', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp', 'user')
    search_fields = ('user__username', 'object_repr', 'ip_address')
    readonly_fields = ('user', 'action', 'content_type', 'object_id', 'object_repr',
                      'changes', 'timestamp', 'ip_address', 'user_agent', 'additional_data')
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        """Disable manual creation of audit logs."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable editing of audit logs."""
        return False

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    """Admin interface for SystemSetting model."""
    list_display = ('key', 'value_type', 'category', 'is_public', 'updated_at')
    list_filter = ('value_type', 'category', 'is_public')
    search_fields = ('key', 'value', 'description')
    fieldsets = (
        (None, {
            'fields': ('key', 'value', 'value_type')
        }),
        ('Metadata', {
            'fields': ('description', 'category', 'is_public')
        }),
    )
