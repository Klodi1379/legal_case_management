# clients/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User  # Import the custom User model
from core.fields import EncryptedCharField, EncryptedTextField

class Client(models.Model):
    """
    Client model for legal case management system.
    Can represent individual clients or organizations.

    Sensitive personal information is stored encrypted.
    """
    CLIENT_TYPE_CHOICES = [
        ('INDIVIDUAL', 'Individual'),
        ('ORGANIZATION', 'Organization'),
    ]

    # Removed encryption salt field as we're using global encryption key

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clients')
    client_type = models.CharField(_('Client Type'), max_length=20, choices=CLIENT_TYPE_CHOICES, default='INDIVIDUAL')

    # Individual client fields - encrypted for privacy
    first_name = EncryptedCharField(_('First Name'), max_length=100, blank=True)
    last_name = EncryptedCharField(_('Last Name'), max_length=100, blank=True)
    date_of_birth = models.DateField(_('Date of Birth'), null=True, blank=True)
    ssn_last_four = EncryptedCharField(_('Last 4 of SSN'), max_length=4, blank=True)

    # Organization client fields
    company_name = EncryptedCharField(_('Company Name'), max_length=255, blank=True)
    industry = models.CharField(_('Industry'), max_length=100, blank=True)
    tax_id = EncryptedCharField(_('Tax ID'), max_length=50, blank=True)

    # Common fields - contact info is sensitive and encrypted
    email = EncryptedCharField(_('Email'), max_length=254, blank=True)
    phone = EncryptedCharField(_('Phone'), max_length=20, blank=True)
    mobile = EncryptedCharField(_('Mobile'), max_length=20, blank=True)
    address_line1 = EncryptedCharField(_('Address Line 1'), max_length=255, blank=True)
    address_line2 = EncryptedCharField(_('Address Line 2'), max_length=255, blank=True)
    city = EncryptedCharField(_('City'), max_length=100, blank=True)
    state = EncryptedCharField(_('State/Province'), max_length=100, blank=True)
    postal_code = EncryptedCharField(_('Postal Code'), max_length=20, blank=True)
    country = EncryptedCharField(_('Country'), max_length=100, blank=True)

    notes = EncryptedTextField(_('Notes'), blank=True)
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    def __str__(self):
        if self.client_type == 'INDIVIDUAL':
            if self.first_name or self.last_name:
                return f"{self.first_name} {self.last_name}".strip()
            return f"Client #{self.id}"
        else:
            return self.company_name or f"Organization #{self.id}"

    def get_full_address(self):
        """Return the full address as a formatted string."""
        address_parts = [
            self.address_line1,
            self.address_line2,
            f"{self.city}, {self.state} {self.postal_code}".strip(),
            self.country
        ]
        return "\n".join(filter(None, address_parts))

    def get_display_name(self):
        """Return the appropriate display name based on client type."""
        if self.client_type == 'INDIVIDUAL':
            return f"{self.first_name} {self.last_name}".strip()
        else:
            return self.company_name

    class Meta:
        verbose_name = _('Client')
        verbose_name_plural = _('Clients')
        ordering = ['last_name', 'first_name', 'company_name']

class ClientContact(models.Model):
    """
    Additional contacts for organizational clients.

    Sensitive personal information is stored encrypted.
    """
    # Removed encryption salt field as we're using global encryption key

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contacts')
    first_name = EncryptedCharField(_('First Name'), max_length=100)
    last_name = EncryptedCharField(_('Last Name'), max_length=100)
    position = models.CharField(_('Position'), max_length=100, blank=True)
    email = EncryptedCharField(_('Email'), max_length=254, blank=True)
    phone = EncryptedCharField(_('Phone'), max_length=20, blank=True)
    mobile = EncryptedCharField(_('Mobile'), max_length=20, blank=True)
    is_primary_contact = models.BooleanField(_('Primary Contact'), default=False)
    notes = EncryptedTextField(_('Notes'), blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        # If this contact is set as primary, unset any other primary contacts
        if self.is_primary_contact:
            ClientContact.objects.filter(
                client=self.client,
                is_primary_contact=True
            ).exclude(id=self.id).update(is_primary_contact=False)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Client Contact')
        verbose_name_plural = _('Client Contacts')
        ordering = ['last_name', 'first_name']