from django.db import models
from django.conf import settings
from cases.models import Case

class Document(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='case_documents/')
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='documents')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)  # Changed from upload_date to uploaded_at
    description = models.TextField(blank=True)
    document_type = models.CharField(max_length=50, blank=True)  # Assuming you want to keep this field

    def __str__(self):
        return self.title