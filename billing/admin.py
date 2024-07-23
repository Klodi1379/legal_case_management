from django.contrib import admin
from .models import TimeEntry, Invoice, InvoiceItem, Payment

@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('case', 'user', 'date', 'hours', 'rate', 'total', 'is_billable')
    list_filter = ('case', 'user', 'date', 'is_billable')
    search_fields = ('case__name', 'user__username', 'description')
    date_hierarchy = 'date'
    readonly_fields = ('total',)

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'case', 'issue_date', 'due_date', 'status', 'subtotal', 'tax', 'total')
    list_filter = ('status', 'issue_date', 'due_date')
    search_fields = ('invoice_number', 'case__name')
    date_hierarchy = 'issue_date'
    readonly_fields = ('total',)
    inlines = [InvoiceItemInline, PaymentInline]

    def save_model(self, request, obj, form, change):
        obj.total = obj.subtotal + obj.tax
        super().save_model(request, obj, form, change)

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'description', 'quantity', 'rate', 'amount')
    list_filter = ('invoice',)
    search_fields = ('invoice__invoice_number', 'description')
    readonly_fields = ('amount',)

    def save_model(self, request, obj, form, change):
        obj.amount = obj.quantity * obj.rate
        super().save_model(request, obj, form, change)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount', 'payment_date', 'payment_method', 'transaction_id')
    list_filter = ('payment_date', 'payment_method')
    search_fields = ('invoice__invoice_number', 'transaction_id')
    date_hierarchy = 'payment_date'