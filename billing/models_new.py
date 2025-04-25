# billing/models_new.py
from django.db import models
from django.conf import settings
from cases.models import Case

class TimeEntryNew(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='time_entries_new')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField()
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    is_billable = models.BooleanField(default=True)

    @property
    def total(self):
        if self.hours is not None and self.rate is not None:
            return self.hours * self.rate
        return 0

    def __str__(self):
        return f"{self.case} - {self.date} - {self.hours} hours"
