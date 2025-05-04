from django.contrib import admin
from .models import PortalAccess, ClientTask, MessageThread, Message, Notification

@admin.register(PortalAccess)
class PortalAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active', 'last_login')
    list_filter = ('is_active',)
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')

@admin.register(ClientTask)
class ClientTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'case', 'assigned_to', 'due_date', 'status', 'is_overdue')
    list_filter = ('status', 'due_date')
    search_fields = ('title', 'description', 'case__title', 'assigned_to__username')
    date_hierarchy = 'due_date'

@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ('subject', 'case', 'created_by', 'created_at', 'updated_at', 'is_closed')
    list_filter = ('is_closed', 'created_at')
    search_fields = ('subject', 'case__title', 'created_by__username')
    date_hierarchy = 'created_at'
    filter_horizontal = ('participants',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('thread', 'sender', 'created_at', 'get_read_count')
    list_filter = ('created_at',)
    search_fields = ('content', 'thread__subject', 'sender__username')
    date_hierarchy = 'created_at'
    filter_horizontal = ('read_by',)

    def get_read_count(self, obj):
        return obj.read_by.count()
    get_read_count.short_description = 'Read by'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'created_at', 'is_read')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    date_hierarchy = 'created_at'
