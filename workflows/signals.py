"""
Signal handlers for workflow events.

This module defines signal handlers for workflow-related events,
such as workflow creation, step transitions, and task completion.
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import WorkflowInstance, WorkflowTask, WorkflowLog

logger = logging.getLogger(__name__)

@receiver(post_save, sender=WorkflowInstance)
def handle_workflow_instance_save(sender, instance, created, **kwargs):
    """
    Handle workflow instance creation and updates.
    
    This signal handler is called when a workflow instance is created or updated.
    It can be used to trigger actions based on workflow state changes.
    
    Args:
        sender: The model class (WorkflowInstance)
        instance: The WorkflowInstance instance that was saved
        created: True if the instance was created, False if it was updated
    """
    if created:
        logger.info(f"New workflow instance created: {instance}")
        
        # Create initial task if the step requires it
        if instance.current_step.action_type in ['MANUAL', 'APPROVAL']:
            # Get task details from step configuration
            task_data = instance.current_step.action_data
            
            # Create the task
            WorkflowTask.objects.create(
                workflow_instance=instance,
                step=instance.current_step,
                title=task_data.get('task_title', f"Action required: {instance.current_step.name}"),
                description=task_data.get('task_description', instance.current_step.description),
                priority=task_data.get('priority', 2),
                assigned_to=instance.created_by,  # Default to workflow creator
                created_by=instance.created_by,
                due_date=timezone.now() + timezone.timedelta(days=task_data.get('due_days', 3))
            )
    else:
        # Handle step changes
        if instance.tracker.has_changed('current_step'):
            old_step = instance.tracker.previous('current_step')
            new_step = instance.current_step
            
            logger.info(f"Workflow instance {instance.id} transitioned from {old_step} to {new_step}")
            
            # Create task for the new step if needed
            if new_step.action_type in ['MANUAL', 'APPROVAL']:
                # Get task details from step configuration
                task_data = new_step.action_data
                
                # Create the task
                WorkflowTask.objects.create(
                    workflow_instance=instance,
                    step=new_step,
                    title=task_data.get('task_title', f"Action required: {new_step.name}"),
                    description=task_data.get('task_description', new_step.description),
                    priority=task_data.get('priority', 2),
                    assigned_to=instance.created_by,  # Default to workflow creator
                    created_by=instance.created_by,
                    due_date=timezone.now() + timezone.timedelta(days=task_data.get('due_days', 3))
                )
        
        # Handle status changes
        if instance.tracker.has_changed('status'):
            old_status = instance.tracker.previous('status')
            new_status = instance.status
            
            logger.info(f"Workflow instance {instance.id} changed status from {old_status} to {new_status}")
            
            if new_status == 'COMPLETED':
                # Mark all pending tasks as canceled
                instance.tasks.filter(status='PENDING').update(
                    status='CANCELED',
                    updated_at=timezone.now()
                )
                
                # Create completion log entry
                WorkflowLog.objects.create(
                    workflow_instance=instance,
                    step=instance.current_step,
                    action="COMPLETED",
                    user=instance.created_by,
                    notes=f"Workflow completed at step: {instance.current_step.name}"
                )


@receiver(post_save, sender=WorkflowTask)
def handle_workflow_task_save(sender, instance, created, **kwargs):
    """
    Handle workflow task creation and updates.
    
    This signal handler is called when a workflow task is created or updated.
    It can be used to trigger notifications or other actions.
    
    Args:
        sender: The model class (WorkflowTask)
        instance: The WorkflowTask instance that was saved
        created: True if the instance was created, False if it was updated
    """
    if created:
        logger.info(f"New workflow task created: {instance}")
        
        # TODO: Send notification to assigned user
        
    else:
        # Handle status changes
        if instance.tracker.has_changed('status'):
            old_status = instance.tracker.previous('status')
            new_status = instance.status
            
            logger.info(f"Workflow task {instance.id} changed status from {old_status} to {new_status}")
            
            if new_status == 'COMPLETED':
                # Check if this completion should trigger a workflow transition
                step = instance.step
                
                # If this step has an automatic transition when tasks are completed,
                # trigger that transition
                auto_transitions = step.outgoing_transitions.filter(
                    condition_type='TASK_COMPLETED',
                    is_active=True
                )
                
                if auto_transitions.exists():
                    transition = auto_transitions.first()
                    instance.workflow_instance.transition_to(
                        transition=transition,
                        user=instance.assigned_to,
                        notes=f"Automatic transition triggered by task completion: {instance.title}"
                    )
