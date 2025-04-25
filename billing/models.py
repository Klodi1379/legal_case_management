# billing/models.py
from django.db import models
from django.conf import settings
from cases.models import Case

class TimeEntry(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='time_entries')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField()
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    is_billable = models.BooleanField(default=True)

    @property
    def total(self):
        if self.hours is not None and self.rate is not None:
            return self.hours * self.rate
        return 0  # or you could return None, depending on your preference

    def __str__(self):
        return f"{self.case} - {self.date} - {self.hours} hours"
    
    
class Invoice(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
    ]
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    
    def save(self, *args, **kwargs):
        if self.subtotal is not None and self.tax is not None:
            self.total = self.subtotal + self.tax
        else:
            self.total = 0  # or None, depending on your preference
        super().save(*args, **kwargs)

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.TextField()
    quantity = models.DecimalField(max_digits=5, decimal_places=2)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if self.quantity is not None and self.rate is not None:
            self.amount = self.quantity * self.rate
        else:
            self.amount = 0  # or None, depending on your preference
        super().save(*args, **kwargs)

class Payment(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)