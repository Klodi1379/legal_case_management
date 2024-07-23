# portal/models.py
from django.db import models
from accounts.models import User
from cases.models import Case

class PortalAccess(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portal_access')
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)

class ClientTask(models.Model):
    TASK_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]
    
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='client_tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks')
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='PENDING')