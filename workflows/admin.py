"""
Admin configuration for workflows app.

This module defines the admin interface for workflow models.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    WorkflowTemplate, WorkflowStep, WorkflowTransition,
    WorkflowInstance, WorkflowLog, WorkflowTask
)

class WorkflowStepInline(admin.TabularInline):
    """Inline admin for workflow steps."""
    model = WorkflowStep
    extra = 1
    fields = ('name', 'action_type', 'is_initial', 'is_final', 'order')

class WorkflowTransitionInline(admin.TabularInline):
    """Inline admin for workflow transitions."""
    model = WorkflowTransition
    extra = 1
    fields = ('name', 'source_step', 'target_step', 'condition_type', 'is_active')

@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    """Admin interface for workflow templates."""
    list_display = ('name', 'content_type', 'is_active', 'created_by', 'created_at')
    list_filter = ('is_active', 'content_type', 'created_at')
    search_fields = ('name', 'description')
    inlines = [WorkflowStepInline, WorkflowTransitionInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active', 'content_type')
        }),
        (_('Audit Information'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    """Admin interface for workflow steps."""
    list_display = ('name', 'template', 'action_type', 'is_initial', 'is_final', 'order')
    list_filter = ('template', 'action_type', 'is_initial', 'is_final')
    search_fields = ('name', 'description', 'template__name')
    fieldsets = (
        (None, {
            'fields': ('template', 'name', 'description', 'action_type', 'action_data')
        }),
        (_('Step Properties'), {
            'fields': ('is_initial', 'is_final', 'order')
        }),
    )

@admin.register(WorkflowTransition)
class WorkflowTransitionAdmin(admin.ModelAdmin):
    """Admin interface for workflow transitions."""
    list_display = ('name', 'template', 'source_step', 'target_step', 'condition_type', 'is_active')
    list_filter = ('template', 'condition_type', 'is_active')
    search_fields = ('name', 'description', 'template__name', 'source_step__name', 'target_step__name')
    fieldsets = (
        (None, {
            'fields': ('template', 'name', 'description')
        }),
        (_('Transition Properties'), {
            'fields': ('source_step', 'target_step', 'condition_type', 'condition_data', 'is_active')
        }),
    )

class WorkflowLogInline(admin.TabularInline):
    """Inline admin for workflow logs."""
    model = WorkflowLog
    extra = 0
    fields = ('action', 'step', 'transition', 'user', 'timestamp', 'notes')
    readonly_fields = ('action', 'step', 'transition', 'user', 'timestamp', 'notes')
    can_delete = False
    max_num = 0

class WorkflowTaskInline(admin.TabularInline):
    """Inline admin for workflow tasks."""
    model = WorkflowTask
    extra = 0
    fields = ('title', 'status', 'priority', 'assigned_to', 'due_date', 'completed_at')
    readonly_fields = ('completed_at',)

@admin.register(WorkflowInstance)
class WorkflowInstanceAdmin(admin.ModelAdmin):
    """Admin interface for workflow instances."""
    list_display = ('template', 'content_object', 'current_step', 'status', 'created_by', 'created_at')
    list_filter = ('template', 'status', 'created_at')
    search_fields = ('template__name', 'created_by__username')
    inlines = [WorkflowTaskInline, WorkflowLogInline]
    fieldsets = (
        (None, {
            'fields': ('template', 'content_type', 'object_id', 'current_step', 'status', 'data')
        }),
        (_('Audit Information'), {
            'fields': ('created_by', 'created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'completed_at')

@admin.register(WorkflowTask)
class WorkflowTaskAdmin(admin.ModelAdmin):
    """Admin interface for workflow tasks."""
    list_display = ('title', 'workflow_instance', 'step', 'status', 'priority', 'assigned_to', 'due_date')
    list_filter = ('status', 'priority', 'created_at', 'due_date')
    search_fields = ('title', 'description', 'workflow_instance__template__name')
    fieldsets = (
        (None, {
            'fields': ('workflow_instance', 'step', 'title', 'description', 'status', 'priority')
        }),
        (_('Assignment'), {
            'fields': ('assigned_to', 'created_by', 'due_date')
        }),
        (_('Completion'), {
            'fields': ('completed_at', 'data'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'completed_at')

@admin.register(WorkflowLog)
class WorkflowLogAdmin(admin.ModelAdmin):
    """Admin interface for workflow logs."""
    list_display = ('workflow_instance', 'action', 'step', 'user', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('workflow_instance__template__name', 'notes', 'user__username')
    fieldsets = (
        (None, {
            'fields': ('workflow_instance', 'step', 'transition', 'action', 'user', 'timestamp')
        }),
        (_('Details'), {
            'fields': ('notes', 'data')
        }),
    )
    readonly_fields = ('workflow_instance', 'step', 'transition', 'action', 'user', 'timestamp')
