# clients/models.py
from django.db import models
from accounts.models import User

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    company_name = models.CharField(max_length=255, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
