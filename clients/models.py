# clients/models.py
from django.db import models
from accounts.models import User  # Import the custom User model

class Client(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    
    def __str__(self):
        return self.company_name