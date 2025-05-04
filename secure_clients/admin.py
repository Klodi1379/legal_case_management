# secure_clients/admin.py
from django.contrib import admin
from .models import SecureClientData, SecureContactData


@admin.register(SecureClientData)
class SecureClientDataAdmin(admin.ModelAdmin):
    """Admin interface for SecureClientData model."""
    list_display = ('client', 'created_at', 'updated_at')
    search_fields = ('client__first_name', 'client__last_name', 'client__company_name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Client Information', {
            'fields': ('client',)
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'ssn_last_four')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'mobile')
        }),
        ('Address Information', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country')
        }),
        ('Organization Information', {
            'fields': ('company_name', 'tax_id')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(SecureContactData)
class SecureContactDataAdmin(admin.ModelAdmin):
    """Admin interface for SecureContactData model."""
    list_display = ('contact', 'created_at', 'updated_at')
    search_fields = ('contact__first_name', 'contact__last_name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Contact Information', {
            'fields': ('contact',)
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name')
        }),
        ('Contact Details', {
            'fields': ('email', 'phone', 'mobile')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
