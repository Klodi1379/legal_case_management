# portal/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from accounts.models import User
from cases.models import Case
from core.fields import EncryptedTextField

class PortalAccess(models.Model):
    """
    Controls access to the client portal for users.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portal_access')
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Portal access for {self.user.username}"

class ClientTask(models.Model):
    """
    Tasks assigned to clients as part of case management.
    """
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.status != 'COMPLETED'

class MessageThread(models.Model):
    """
    Thread for secure messaging between clients and attorneys.
    """
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='message_threads', null=True, blank=True)
    subject = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_threads')
    participants = models.ManyToManyField(User, related_name='message_threads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_closed = models.BooleanField(default=False)

    def __str__(self):
        return self.subject

    def get_latest_message(self):
        return self.messages.order_by('-created_at').first()

    def unread_count(self, user):
        return self.messages.exclude(read_by=user).count()

class Message(models.Model):
    """
    Individual message within a thread. Content is encrypted.
    """
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = EncryptedTextField(_('Message Content'))
    created_at = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(User, related_name='read_messages', blank=True)

    def __str__(self):
        return f"Message from {self.sender.username} at {self.created_at}"

    def mark_as_read(self, user):
        self.read_by.add(user)
        self.save()

class Notification(models.Model):
    """
    Notifications for portal users.
    """
    NOTIFICATION_TYPES = [
        ('MESSAGE', 'New Message'),
        ('DOCUMENT', 'New Document'),
        ('CASE_UPDATE', 'Case Update'),
        ('TASK', 'Task Assignment'),
        ('DEADLINE', 'Upcoming Deadline'),
        ('OTHER', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']