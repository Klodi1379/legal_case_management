# cases/models.py
from django.db import models
from accounts.models import User
from clients.models import Client

class Case(models.Model):
    CASE_STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
        ('PENDING', 'Pending'),
    ]
    CASE_TYPE_CHOICES = [
        ('CIVIL', 'Civil'),
        ('CRIMINAL', 'Criminal'),
        ('CORPORATE', 'Corporate'),
        ('FAMILY', 'Family'),
        ('OTHER', 'Other'),
    ]
    
    title = models.CharField(max_length=255)
    case_number = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='cases')
    assigned_lawyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_cases')
    status = models.CharField(max_length=10, choices=CASE_STATUS_CHOICES, default='OPEN')
    case_type = models.CharField(max_length=20, choices=CASE_TYPE_CHOICES)
    description = models.TextField()
    open_date = models.DateField(auto_now_add=True)
    close_date = models.DateField(null=True, blank=True)

class CaseNote(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)