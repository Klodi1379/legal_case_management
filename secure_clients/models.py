# secure_clients/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.fields import EncryptedCharField, EncryptedTextField
from clients.models import Client

class SecureClientData(models.Model):
    """
    Secure storage for sensitive client data.

    This model stores encrypted versions of sensitive client information.
    """
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='secure_data')

    # Personal information
    first_name = EncryptedCharField(_('First Name'), max_length=100, blank=True)
    last_name = EncryptedCharField(_('Last Name'), max_length=100, blank=True)
    ssn_last_four = EncryptedCharField(_('Last 4 of SSN'), max_length=4, blank=True)

    # Contact information
    email = EncryptedCharField(_('Email'), max_length=254, blank=True)
    phone = EncryptedCharField(_('Phone'), max_length=20, blank=True)
    mobile = EncryptedCharField(_('Mobile'), max_length=20, blank=True)

    # Address information
    address_line1 = EncryptedCharField(_('Address Line 1'), max_length=255, blank=True)
    address_line2 = EncryptedCharField(_('Address Line 2'), max_length=255, blank=True)
    city = EncryptedCharField(_('City'), max_length=100, blank=True)
    state = EncryptedCharField(_('State/Province'), max_length=100, blank=True)
    postal_code = EncryptedCharField(_('Postal Code'), max_length=20, blank=True)
    country = EncryptedCharField(_('Country'), max_length=100, blank=True)

    # Organization information
    company_name = EncryptedCharField(_('Company Name'), max_length=255, blank=True)
    tax_id = EncryptedCharField(_('Tax ID'), max_length=50, blank=True)

    # Notes
    notes = EncryptedTextField(_('Notes'), blank=True)

    # Metadata
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    def __str__(self):
        return f"Secure data for client {self.client_id}"

    class Meta:
        verbose_name = _('Secure Client Data')
        verbose_name_plural = _('Secure Client Data')


class SecureContactData(models.Model):
    """
    Secure storage for sensitive contact data.

    This model stores encrypted versions of sensitive contact information.
    """
    contact = models.OneToOneField('clients.ClientContact', on_delete=models.CASCADE, related_name='secure_data')

    # Personal information
    first_name = EncryptedCharField(_('First Name'), max_length=100, blank=True)
    last_name = EncryptedCharField(_('Last Name'), max_length=100, blank=True)

    # Contact information
    email = EncryptedCharField(_('Email'), max_length=254, blank=True)
    phone = EncryptedCharField(_('Phone'), max_length=20, blank=True)
    mobile = EncryptedCharField(_('Mobile'), max_length=20, blank=True)

    # Notes
    notes = EncryptedTextField(_('Notes'), blank=True)

    # Metadata
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    def __str__(self):
        return f"Secure data for contact {self.contact_id}"

    class Meta:
        verbose_name = _('Secure Contact Data')
        verbose_name_plural = _('Secure Contact Data')
