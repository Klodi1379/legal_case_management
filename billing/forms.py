# billing/forms.py
from django import forms
from .models import TimeEntry, Invoice, InvoiceItem, Payment

class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = ['case', 'date', 'hours', 'description', 'rate', 'is_billable']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['case', 'invoice_number', 'issue_date', 'due_date', 'status', 'subtotal', 'tax']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['description', 'quantity', 'rate']

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_date', 'payment_method', 'transaction_id']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
        }