"""
Views for workflow automation.

This module defines the views for workflow automation, including
workflow templates, instances, and tasks.
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from .models import (
    WorkflowTemplate, WorkflowStep, WorkflowTransition,
    WorkflowInstance, WorkflowLog, WorkflowTask
)

logger = logging.getLogger(__name__)

@login_required
def workflow_dashboard(request):
    """
    Dashboard for workflow automation.
    
    This view displays an overview of workflows, including active
    instances, pending tasks, and available templates.
    """
    # Get active workflow instances for the user
    active_instances = WorkflowInstance.objects.filter(
        Q(created_by=request.user) | Q(tasks__assigned_to=request.user),
        status='ACTIVE'
    ).distinct()
    
    # Get pending tasks assigned to the user
    pending_tasks = WorkflowTask.objects.filter(
        assigned_to=request.user,
        status__in=['PENDING', 'IN_PROGRESS']
    ).order_by('-priority', 'due_date')
    
    # Get available workflow templates
    available_templates = WorkflowTemplate.objects.filter(is_active=True)
    
    # Get recently completed workflows
    completed_instances = WorkflowInstance.objects.filter(
        created_by=request.user,
        status='COMPLETED'
    ).order_by('-completed_at')[:5]
    
    context = {
        'active_instances': active_instances,
        'pending_tasks': pending_tasks,
        'available_templates': available_templates,
        'completed_instances': completed_instances,
    }
    
    return render(request, 'workflows/dashboard.html', context)

@login_required
def workflow_instance_detail(request, instance_id):
    """
    Detail view for a workflow instance.
    
    This view displays the details of a workflow instance, including
    its current step, available transitions, tasks, and logs.
    """
    instance = get_object_or_404(WorkflowInstance, id=instance_id)
    
    # Check if the user has permission to view this instance
    if instance.created_by != request.user and not request.user.is_staff:
        if not instance.tasks.filter(assigned_to=request.user).exists():
            messages.error(request, "You don't have permission to view this workflow.")
            return redirect('workflows:dashboard')
    
    # Get available transitions
    available_transitions = instance.get_available_transitions(request.user)
    
    # Get tasks for this instance
    tasks = instance.tasks.all().order_by('-created_at')
    
    # Get logs for this instance
    logs = instance.logs.all().order_by('-timestamp')
    
    context = {
        'instance': instance,
        'available_transitions': available_transitions,
        'tasks': tasks,
        'logs': logs,
    }
    
    return render(request, 'workflows/instance_detail.html', context)

@login_required
def workflow_transition(request, instance_id, transition_id):
    """
    Transition a workflow instance to the next step.
    
    This view handles the transition of a workflow instance from one
    step to another.
    """
    instance = get_object_or_404(WorkflowInstance, id=instance_id)
    transition = get_object_or_404(WorkflowTransition, id=transition_id)
    
    # Check if the user has permission to perform this transition
    if instance.created_by != request.user and not request.user.is_staff:
        if not instance.tasks.filter(assigned_to=request.user).exists():
            messages.error(request, "You don't have permission to perform this action.")
            return redirect('workflows:instance_detail', instance_id=instance.id)
    
    # Get notes from the form
    notes = request.POST.get('notes', '')
    
    # Perform the transition
    success = instance.transition_to(transition, request.user, notes)
    
    if success:
        messages.success(request, f"Workflow transitioned to {instance.current_step.name}.")
    else:
        messages.error(request, "Failed to transition the workflow. Please try again.")
    
    return redirect('workflows:instance_detail', instance_id=instance.id)

@login_required
def workflow_task_detail(request, task_id):
    """
    Detail view for a workflow task.
    
    This view displays the details of a workflow task and allows the
    user to update its status.
    """
    task = get_object_or_404(WorkflowTask, id=task_id)
    
    # Check if the user has permission to view this task
    if task.assigned_to != request.user and task.created_by != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to view this task.")
        return redirect('workflows:dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        if action == 'complete':
            # Complete the task
            task.status = 'COMPLETED'
            task.completed_at = timezone.now()
            task.save()
            
            # Create log entry
            WorkflowLog.objects.create(
                workflow_instance=task.workflow_instance,
                step=task.step,
                action="CUSTOM",
                user=request.user,
                notes=notes or f"Task '{task.title}' completed",
                data={"task_id": task.id, "task_action": "completed"}
            )
            
            messages.success(request, "Task marked as completed.")
            return redirect('workflows:instance_detail', instance_id=task.workflow_instance.id)
            
        elif action == 'start':
            # Start working on the task
            task.status = 'IN_PROGRESS'
            task.save()
            
            # Create log entry
            WorkflowLog.objects.create(
                workflow_instance=task.workflow_instance,
                step=task.step,
                action="CUSTOM",
                user=request.user,
                notes=f"Started working on task '{task.title}'",
                data={"task_id": task.id, "task_action": "started"}
            )
            
            messages.success(request, "Task marked as in progress.")
    
    context = {
        'task': task,
    }
    
    return render(request, 'workflows/task_detail.html', context)

@login_required
def workflow_task_list(request):
    """
    List view for workflow tasks.
    
    This view displays a list of workflow tasks assigned to the user.
    """
    # Get tasks assigned to the user
    tasks = WorkflowTask.objects.filter(
        assigned_to=request.user
    ).order_by('status', '-priority', 'due_date')
    
    context = {
        'tasks': tasks,
    }
    
    return render(request, 'workflows/task_list.html', context)

@login_required
def create_workflow(request, content_type_id, object_id):
    """
    Create a new workflow instance.
    
    This view allows the user to create a new workflow instance for
    a specific object.
    """
    content_type = get_object_or_404(ContentType, id=content_type_id)
    
    # Get the object
    try:
        content_object = content_type.get_object_for_this_type(id=object_id)
    except:
        messages.error(request, "The specified object does not exist.")
        return redirect('workflows:dashboard')
    
    # Get available templates for this content type
    templates = WorkflowTemplate.objects.filter(
        content_type=content_type,
        is_active=True
    )
    
    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        
        if not template_id:
            messages.error(request, "Please select a workflow template.")
            return render(request, 'workflows/create_workflow.html', {
                'content_object': content_object,
                'templates': templates,
            })
        
        template = get_object_or_404(WorkflowTemplate, id=template_id)
        
        try:
            # Create the workflow instance
            instance = template.create_instance(content_object, request.user)
            
            messages.success(request, f"Workflow '{template.name}' started successfully.")
            return redirect('workflows:instance_detail', instance_id=instance.id)
            
        except Exception as e:
            logger.error(f"Error creating workflow instance: {str(e)}", exc_info=True)
            messages.error(request, f"Error creating workflow: {str(e)}")
    
    context = {
        'content_object': content_object,
        'templates': templates,
    }
    
    return render(request, 'workflows/create_workflow.html', context)
