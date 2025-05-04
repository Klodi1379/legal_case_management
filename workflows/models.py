"""
Models for workflow automation.

This module defines the database models for workflow automation,
including workflow templates, steps, transitions, and instances.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class WorkflowTemplate(models.Model):
    """
    Template for a workflow process.
    
    A workflow template defines the structure of a workflow process,
    including its steps, transitions, and conditions.
    """
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_workflows",
        verbose_name=_("Created By")
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    # Content type this workflow applies to (e.g., Case, Document)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("Content Type"),
        help_text=_("The type of object this workflow applies to")
    )
    
    class Meta:
        verbose_name = _("Workflow Template")
        verbose_name_plural = _("Workflow Templates")
        ordering = ["name"]
    
    def __str__(self):
        return self.name
    
    def get_initial_step(self):
        """Get the initial step of this workflow."""
        return self.steps.filter(is_initial=True).first()
    
    def get_final_steps(self):
        """Get all final steps of this workflow."""
        return self.steps.filter(is_final=True)
    
    def create_instance(self, content_object, user):
        """
        Create a new workflow instance for the given object.
        
        Args:
            content_object: The object to create a workflow for
            user: The user creating the workflow
            
        Returns:
            The created WorkflowInstance
        """
        initial_step = self.get_initial_step()
        if not initial_step:
            raise ValueError("Workflow template has no initial step")
        
        instance = WorkflowInstance.objects.create(
            template=self,
            content_type=ContentType.objects.get_for_model(content_object),
            object_id=content_object.id,
            created_by=user,
            current_step=initial_step
        )
        
        # Create initial log entry
        WorkflowLog.objects.create(
            workflow_instance=instance,
            step=initial_step,
            action="CREATED",
            user=user,
            notes=f"Workflow started at step: {initial_step.name}"
        )
        
        return instance


class WorkflowStep(models.Model):
    """
    Step in a workflow process.
    
    A workflow step represents a state in the workflow process.
    """
    ACTION_CHOICES = (
        ('MANUAL', 'Manual Action Required'),
        ('AUTOMATIC', 'Automatic'),
        ('NOTIFICATION', 'Send Notification'),
        ('APPROVAL', 'Approval Required'),
        ('DOCUMENT', 'Document Generation'),
        ('CUSTOM', 'Custom Action'),
    )
    
    template = models.ForeignKey(
        WorkflowTemplate,
        on_delete=models.CASCADE,
        related_name="steps",
        verbose_name=_("Workflow Template")
    )
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    action_type = models.CharField(_("Action Type"), max_length=20, choices=ACTION_CHOICES)
    action_data = models.JSONField(_("Action Data"), default=dict, blank=True)
    is_initial = models.BooleanField(_("Is Initial Step"), default=False)
    is_final = models.BooleanField(_("Is Final Step"), default=False)
    order = models.PositiveIntegerField(_("Order"), default=0)
    
    class Meta:
        verbose_name = _("Workflow Step")
        verbose_name_plural = _("Workflow Steps")
        ordering = ["template", "order"]
        unique_together = [["template", "name"]]
    
    def __str__(self):
        return f"{self.template.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        """Override save to ensure only one initial step per workflow."""
        if self.is_initial:
            # Set all other steps as non-initial
            WorkflowStep.objects.filter(
                template=self.template, 
                is_initial=True
            ).exclude(pk=self.pk).update(is_initial=False)
        
        super().save(*args, **kwargs)
    
    def get_available_transitions(self):
        """Get all available transitions from this step."""
        return self.outgoing_transitions.filter(is_active=True)


class WorkflowTransition(models.Model):
    """
    Transition between workflow steps.
    
    A workflow transition represents a possible path from one step to another.
    """
    CONDITION_TYPE_CHOICES = (
        ('NONE', 'No Condition'),
        ('USER_ROLE', 'User Role'),
        ('FIELD_VALUE', 'Field Value'),
        ('TIME_BASED', 'Time Based'),
        ('CUSTOM', 'Custom Condition'),
    )
    
    template = models.ForeignKey(
        WorkflowTemplate,
        on_delete=models.CASCADE,
        related_name="transitions",
        verbose_name=_("Workflow Template")
    )
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    source_step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.CASCADE,
        related_name="outgoing_transitions",
        verbose_name=_("Source Step")
    )
    target_step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.CASCADE,
        related_name="incoming_transitions",
        verbose_name=_("Target Step")
    )
    condition_type = models.CharField(_("Condition Type"), max_length=20, choices=CONDITION_TYPE_CHOICES, default='NONE')
    condition_data = models.JSONField(_("Condition Data"), default=dict, blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    
    class Meta:
        verbose_name = _("Workflow Transition")
        verbose_name_plural = _("Workflow Transitions")
        ordering = ["template", "source_step", "name"]
        unique_together = [["template", "source_step", "name"]]
    
    def __str__(self):
        return f"{self.source_step.name} → {self.target_step.name}"
    
    def check_condition(self, workflow_instance, user=None):
        """
        Check if the condition for this transition is met.
        
        Args:
            workflow_instance: The workflow instance
            user: The user performing the transition (if applicable)
            
        Returns:
            True if the condition is met, False otherwise
        """
        if self.condition_type == 'NONE':
            return True
        
        if self.condition_type == 'USER_ROLE':
            if not user:
                return False
            
            required_roles = self.condition_data.get('roles', [])
            user_roles = [group.name for group in user.groups.all()]
            
            return any(role in user_roles for role in required_roles)
        
        # Implement other condition types as needed
        
        return False


class WorkflowInstance(models.Model):
    """
    Instance of a workflow process.
    
    A workflow instance represents a specific execution of a workflow template
    for a specific object.
    """
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELED', 'Canceled'),
        ('SUSPENDED', 'Suspended'),
    )
    
    template = models.ForeignKey(
        WorkflowTemplate,
        on_delete=models.CASCADE,
        related_name="instances",
        verbose_name=_("Workflow Template")
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("Content Type")
    )
    object_id = models.PositiveIntegerField(_("Object ID"))
    content_object = GenericForeignKey('content_type', 'object_id')
    
    current_step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.CASCADE,
        related_name="instances",
        verbose_name=_("Current Step")
    )
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    data = models.JSONField(_("Instance Data"), default=dict, blank=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="initiated_workflows",
        verbose_name=_("Created By")
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    completed_at = models.DateTimeField(_("Completed At"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Workflow Instance")
        verbose_name_plural = _("Workflow Instances")
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.template.name} for {self.content_object}"
    
    def get_available_transitions(self, user=None):
        """
        Get all available transitions from the current step.
        
        Args:
            user: The user to check permissions for
            
        Returns:
            QuerySet of available transitions
        """
        transitions = self.current_step.get_available_transitions()
        
        if user:
            # Filter transitions based on user permissions
            return [t for t in transitions if t.check_condition(self, user)]
        
        return transitions
    
    def transition_to(self, transition, user, notes=None):
        """
        Transition to the next step.
        
        Args:
            transition: The transition to follow
            user: The user performing the transition
            notes: Optional notes about the transition
            
        Returns:
            True if the transition was successful, False otherwise
        """
        if self.status != 'ACTIVE':
            return False
        
        if transition not in self.get_available_transitions(user):
            return False
        
        # Update current step
        old_step = self.current_step
        self.current_step = transition.target_step
        
        # Check if we've reached a final step
        if self.current_step.is_final:
            self.status = 'COMPLETED'
            self.completed_at = timezone.now()
        
        self.save()
        
        # Create log entry
        WorkflowLog.objects.create(
            workflow_instance=self,
            step=self.current_step,
            transition=transition,
            action="TRANSITION",
            user=user,
            notes=notes or f"Transitioned from {old_step.name} to {self.current_step.name}"
        )
        
        return True


class WorkflowLog(models.Model):
    """
    Log entry for a workflow instance.
    
    A workflow log entry records an action or event in a workflow instance.
    """
    ACTION_CHOICES = (
        ('CREATED', 'Workflow Created'),
        ('TRANSITION', 'Step Transition'),
        ('COMMENT', 'Comment Added'),
        ('DOCUMENT', 'Document Generated'),
        ('NOTIFICATION', 'Notification Sent'),
        ('APPROVAL', 'Approval Action'),
        ('REJECTION', 'Rejection Action'),
        ('CUSTOM', 'Custom Action'),
        ('COMPLETED', 'Workflow Completed'),
        ('CANCELED', 'Workflow Canceled'),
    )
    
    workflow_instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name="logs",
        verbose_name=_("Workflow Instance")
    )
    step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.CASCADE,
        related_name="logs",
        verbose_name=_("Workflow Step")
    )
    transition = models.ForeignKey(
        WorkflowTransition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs",
        verbose_name=_("Workflow Transition")
    )
    action = models.CharField(_("Action"), max_length=20, choices=ACTION_CHOICES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="workflow_logs",
        verbose_name=_("User")
    )
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True)
    notes = models.TextField(_("Notes"), blank=True)
    data = models.JSONField(_("Additional Data"), default=dict, blank=True)
    
    class Meta:
        verbose_name = _("Workflow Log")
        verbose_name_plural = _("Workflow Logs")
        ordering = ["workflow_instance", "timestamp"]
    
    def __str__(self):
        return f"{self.get_action_display()} at {self.timestamp}"


class WorkflowTask(models.Model):
    """
    Task generated by a workflow.
    
    A workflow task represents an action that needs to be performed
    as part of a workflow process.
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELED', 'Canceled'),
    )
    
    PRIORITY_CHOICES = (
        (1, 'Low'),
        (2, 'Normal'),
        (3, 'High'),
        (4, 'Urgent'),
    )
    
    workflow_instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name=_("Workflow Instance")
    )
    step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name=_("Workflow Step")
    )
    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='PENDING')
    priority = models.IntegerField(_("Priority"), choices=PRIORITY_CHOICES, default=2)
    
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_workflow_tasks",
        verbose_name=_("Assigned To")
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_workflow_tasks",
        verbose_name=_("Created By")
    )
    
    due_date = models.DateTimeField(_("Due Date"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    completed_at = models.DateTimeField(_("Completed At"), null=True, blank=True)
    
    data = models.JSONField(_("Task Data"), default=dict, blank=True)
    
    class Meta:
        verbose_name = _("Workflow Task")
        verbose_name_plural = _("Workflow Tasks")
        ordering = ["-priority", "due_date", "-created_at"]
    
    def __str__(self):
        return self.title
    
    def complete(self, user, notes=None):
        """
        Mark the task as completed.
        
        Args:
            user: The user completing the task
            notes: Optional notes about the completion
            
        Returns:
            True if the task was completed, False otherwise
        """
        if self.status in ['COMPLETED', 'CANCELED']:
            return False
        
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save()
        
        # Create log entry
        WorkflowLog.objects.create(
            workflow_instance=self.workflow_instance,
            step=self.step,
            action="CUSTOM",
            user=user,
            notes=notes or f"Task '{self.title}' completed",
            data={"task_id": self.id, "task_action": "completed"}
        )
        
        return True
