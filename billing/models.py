# billing/models.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from cases.models import Case
import uuid
from decimal import Decimal

class ActivityCode(models.Model):
    """
    Standard activity codes for legal billing.
    """
    code = models.CharField(_('Code'), max_length=20, unique=True)
    description = models.CharField(_('Description'), max_length=255)
    is_active = models.BooleanField(_('Active'), default=True)

    def __str__(self):
        return f"{self.code} - {self.description}"

    class Meta:
        verbose_name = _('Activity Code')
        verbose_name_plural = _('Activity Codes')
        ordering = ['code']

class ExpenseCategory(models.Model):
    """
    Categories for legal expenses.
    """
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    is_billable = models.BooleanField(_('Billable by Default'), default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Expense Category')
        verbose_name_plural = _('Expense Categories')
        ordering = ['name']

class TimeEntry(models.Model):
    """
    Time tracking for billable hours.
    """
    BILLING_STATUS_CHOICES = [
        ('BILLABLE', 'Billable'),
        ('NON_BILLABLE', 'Non-Billable'),
        ('NO_CHARGE', 'No Charge'),
    ]

    # Basic information
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='time_entries', verbose_name=_('Case'))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('Timekeeper'))
    activity_code = models.ForeignKey(ActivityCode, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='time_entries', verbose_name=_('Activity Code'))

    # Time details
    date = models.DateField(_('Date'))
    start_time = models.TimeField(_('Start Time'), null=True, blank=True)
    end_time = models.TimeField(_('End Time'), null=True, blank=True)
    hours = models.DecimalField(_('Hours'), max_digits=5, decimal_places=2)
    description = models.TextField(_('Description'))

    # Billing details
    rate = models.DecimalField(_('Rate'), max_digits=10, decimal_places=2)
    billing_status = models.CharField(_('Billing Status'), max_length=20, choices=BILLING_STATUS_CHOICES, default='BILLABLE')
    is_billable = models.BooleanField(_('Billable'), default=True)

    # Invoice status
    is_billed = models.BooleanField(_('Billed'), default=False)
    invoice = models.ForeignKey('Invoice', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='time_entries', verbose_name=_('Invoice'))

    # Metadata
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    @property
    def total(self):
        """Calculate the total amount for this time entry."""
        if self.hours is not None and self.rate is not None:
            return self.hours * self.rate
        return Decimal('0.00')

    def __str__(self):
        return f"{self.case} - {self.date} - {self.hours} hours"

    def save(self, *args, **kwargs):
        # Calculate hours from start and end time if provided
        if self.start_time and self.end_time and not self.hours:
            # Convert time objects to datetime for calculation
            start_dt = timezone.now().replace(hour=self.start_time.hour,
                                             minute=self.start_time.minute,
                                             second=self.start_time.second)
            end_dt = timezone.now().replace(hour=self.end_time.hour,
                                           minute=self.end_time.minute,
                                           second=self.end_time.second)

            # Handle case where end time is on the next day
            if end_dt < start_dt:
                end_dt = end_dt.replace(day=end_dt.day + 1)

            # Calculate duration in hours
            duration = (end_dt - start_dt).total_seconds() / 3600
            self.hours = Decimal(str(round(duration, 2)))

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Time Entry')
        verbose_name_plural = _('Time Entries')
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['case', '-date']),
            models.Index(fields=['user', '-date']),
            models.Index(fields=['is_billed']),
        ]

class Expense(models.Model):
    """
    Expenses incurred on behalf of clients.
    """
    # Basic information
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='expenses', verbose_name=_('Case'))
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True,
                                related_name='expenses', verbose_name=_('Category'))
    description = models.CharField(_('Description'), max_length=255)

    # Financial details
    amount = models.DecimalField(_('Amount'), max_digits=10, decimal_places=2)
    tax = models.DecimalField(_('Tax'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    date = models.DateField(_('Date'))

    # Receipt
    receipt = models.FileField(_('Receipt'), upload_to='expense_receipts/', null=True, blank=True)

    # Billing status
    is_billable = models.BooleanField(_('Billable'), default=True)
    is_billed = models.BooleanField(_('Billed'), default=False)
    invoice = models.ForeignKey('Invoice', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='expenses', verbose_name=_('Invoice'))

    # Metadata
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='created_expenses', verbose_name=_('Created By'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    @property
    def total(self):
        """Calculate the total amount including tax."""
        if self.amount is not None and self.tax is not None:
            return self.amount + self.tax
        return self.amount or Decimal('0.00')

    def __str__(self):
        return f"{self.case} - {self.description} - ${self.amount}"

    class Meta:
        verbose_name = _('Expense')
        verbose_name_plural = _('Expenses')
        ordering = ['-date']

class Invoice(models.Model):
    """
    Client invoices for legal services.
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('PAID', 'Paid'),
        ('PARTIAL', 'Partially Paid'),
        ('OVERDUE', 'Overdue'),
        ('VOID', 'Void'),
    ]

    # Basic information
    invoice_number = models.CharField(_('Invoice Number'), max_length=50, unique=True)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='invoices', verbose_name=_('Case'))

    # Dates
    issue_date = models.DateField(_('Issue Date'))
    due_date = models.DateField(_('Due Date'))

    # Financial details
    subtotal = models.DecimalField(_('Subtotal'), max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(_('Tax Rate %'), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    tax = models.DecimalField(_('Tax Amount'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount = models.DecimalField(_('Discount'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(_('Total'), max_digits=10, decimal_places=2)

    # Status
    status = models.CharField(_('Status'), max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    notes = models.TextField(_('Notes'), blank=True)

    # Metadata
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='created_invoices', verbose_name=_('Created By'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    def save(self, *args, **kwargs):
        # Calculate tax and total
        if self.subtotal is not None:
            if self.tax_rate is not None:
                self.tax = self.subtotal * (self.tax_rate / Decimal('100.0'))
            else:
                self.tax = Decimal('0.00')

            self.total = self.subtotal + self.tax - (self.discount or Decimal('0.00'))
        else:
            self.total = Decimal('0.00')

        super().save(*args, **kwargs)

    @property
    def amount_paid(self):
        """Calculate the total amount paid on this invoice."""
        return self.payments.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    @property
    def balance_due(self):
        """Calculate the remaining balance due on this invoice."""
        return self.total - self.amount_paid

    def update_status(self):
        """Update the invoice status based on payments and due date."""
        if self.status == 'VOID':
            return

        amount_paid = self.amount_paid

        if amount_paid >= self.total:
            self.status = 'PAID'
        elif amount_paid > 0:
            self.status = 'PARTIAL'
        elif self.due_date < timezone.now().date() and self.status != 'DRAFT':
            self.status = 'OVERDUE'

        self.save()

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.case}"

    class Meta:
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')
        ordering = ['-issue_date']

class InvoiceItem(models.Model):
    """
    Line items on an invoice.
    """
    ITEM_TYPE_CHOICES = [
        ('TIME', 'Time Entry'),
        ('EXPENSE', 'Expense'),
        ('FLAT_FEE', 'Flat Fee'),
        ('OTHER', 'Other'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items', verbose_name=_('Invoice'))
    item_type = models.CharField(_('Item Type'), max_length=10, choices=ITEM_TYPE_CHOICES, default='TIME')
    description = models.TextField(_('Description'))
    quantity = models.DecimalField(_('Quantity'), max_digits=8, decimal_places=2)
    rate = models.DecimalField(_('Rate'), max_digits=10, decimal_places=2)
    amount = models.DecimalField(_('Amount'), max_digits=10, decimal_places=2)

    # Optional references to source items
    time_entry = models.ForeignKey(TimeEntry, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='invoice_items', verbose_name=_('Time Entry'))
    expense = models.ForeignKey(Expense, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='invoice_items', verbose_name=_('Expense'))

    def save(self, *args, **kwargs):
        # Calculate amount
        if self.quantity is not None and self.rate is not None:
            self.amount = self.quantity * self.rate
        else:
            self.amount = Decimal('0.00')

        super().save(*args, **kwargs)

        # Update invoice totals
        self.invoice.subtotal = self.invoice.items.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        self.invoice.save()

    def __str__(self):
        return f"{self.description} - {self.amount}"

    class Meta:
        verbose_name = _('Invoice Item')
        verbose_name_plural = _('Invoice Items')

class Payment(models.Model):
    """
    Payments received for invoices.
    """
    PAYMENT_METHOD_CHOICES = [
        ('CHECK', 'Check'),
        ('CREDIT_CARD', 'Credit Card'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CASH', 'Cash'),
        ('OTHER', 'Other'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', verbose_name=_('Invoice'))
    amount = models.DecimalField(_('Amount'), max_digits=10, decimal_places=2)
    payment_date = models.DateField(_('Payment Date'))
    payment_method = models.CharField(_('Payment Method'), max_length=20, choices=PAYMENT_METHOD_CHOICES)
    reference_number = models.CharField(_('Reference Number'), max_length=100, blank=True)
    notes = models.TextField(_('Notes'), blank=True)

    # Metadata
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='received_payments', verbose_name=_('Received By'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update invoice status after payment
        self.invoice.update_status()

    def __str__(self):
        return f"Payment of ${self.amount} for Invoice #{self.invoice.invoice_number}"

    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        ordering = ['-payment_date']

class TrustAccount(models.Model):
    """
    Trust account for client funds.
    """
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, related_name='trust_accounts', verbose_name=_('Client'))
    account_number = models.CharField(_('Account Number'), max_length=50, unique=True)
    description = models.CharField(_('Description'), max_length=255, blank=True)
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    @property
    def current_balance(self):
        """Calculate the current balance of the trust account."""
        deposits = self.transactions.filter(transaction_type='DEPOSIT').aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        withdrawals = self.transactions.filter(transaction_type='WITHDRAWAL').aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        return deposits - withdrawals

    def __str__(self):
        return f"Trust Account #{self.account_number} - {self.client}"

    class Meta:
        verbose_name = _('Trust Account')
        verbose_name_plural = _('Trust Accounts')

class TrustTransaction(models.Model):
    """
    Transactions for trust accounts.
    """
    TRANSACTION_TYPE_CHOICES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
    ]

    trust_account = models.ForeignKey(TrustAccount, on_delete=models.CASCADE, related_name='transactions', verbose_name=_('Trust Account'))
    transaction_type = models.CharField(_('Transaction Type'), max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(_('Amount'), max_digits=10, decimal_places=2)
    date = models.DateField(_('Date'))
    description = models.CharField(_('Description'), max_length=255)
    reference_number = models.CharField(_('Reference Number'), max_length=100, blank=True)

    # Optional references
    case = models.ForeignKey('cases.Case', on_delete=models.SET_NULL, null=True, blank=True,
                            related_name='trust_transactions', verbose_name=_('Case'))
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='trust_transactions', verbose_name=_('Invoice'))

    # Metadata
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='created_trust_transactions', verbose_name=_('Created By'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()} of ${self.amount} on {self.date}"

    class Meta:
        verbose_name = _('Trust Transaction')
        verbose_name_plural = _('Trust Transactions')
        ordering = ['-date', '-created_at']