"""
URL patterns for workflow automation.

This module defines the URL patterns for workflow automation views.
"""

from django.urls import path
from . import views

app_name = 'workflows'

urlpatterns = [
    # Dashboard
    path('', views.workflow_dashboard, name='dashboard'),
    
    # Workflow instances
    path('instances/<int:instance_id>/', views.workflow_instance_detail, name='instance_detail'),
    path('instances/<int:instance_id>/transition/<int:transition_id>/', views.workflow_transition, name='transition'),
    
    # Workflow tasks
    path('tasks/', views.workflow_task_list, name='task_list'),
    path('tasks/<int:task_id>/', views.workflow_task_detail, name='task_detail'),
    
    # Create workflow
    path('create/<int:content_type_id>/<int:object_id>/', views.create_workflow, name='create_workflow'),
]
