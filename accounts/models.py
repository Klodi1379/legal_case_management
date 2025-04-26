# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Extended user model for legal case management system.
    Includes roles and additional information for legal professionals.
    """
    ROLE_CHOICES = [
        ('ATTORNEY', 'Attorney'),
        ('PARALEGAL', 'Paralegal'),
        ('LEGAL_ASSISTANT', 'Legal Assistant'),
        ('ADMIN', 'Administrator'),
        ('CLIENT', 'Client'),
        ('OTHER', 'Other'),
    ]

    role = models.CharField(_('Role'), max_length=20, choices=ROLE_CHOICES, default='OTHER')
    is_client = models.BooleanField(_('Is Client'), default=False)
    is_lawyer = models.BooleanField(_('Is Lawyer'), default=False)
    phone_number = models.CharField(_('Phone Number'), max_length=20, blank=True)
    mobile_number = models.CharField(_('Mobile Number'), max_length=20, blank=True)
    address = models.TextField(_('Address'), blank=True)
    bar_number = models.CharField(_('Bar Number'), max_length=50, blank=True)
    practice_areas = models.CharField(_('Practice Areas'), max_length=255, blank=True)
    hourly_rate = models.DecimalField(_('Hourly Rate'), max_digits=10, decimal_places=2, null=True, blank=True)
    bio = models.TextField(_('Biography'), blank=True)
    profile_image = models.ImageField(_('Profile Image'), upload_to='profile_images/', null=True, blank=True)

    # Add related_name to avoid clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )

    def is_attorney(self):
        """Check if user is an attorney."""
        return self.role == 'ATTORNEY' or self.is_lawyer

    def is_staff_member(self):
        """Check if user is a staff member (not a client)."""
        return not self.is_client

    def get_full_name_with_role(self):
        """Return full name with role for display purposes."""
        full_name = self.get_full_name()
        if self.role:
            role_display = dict(self.ROLE_CHOICES).get(self.role, '')
            return f"{full_name} ({role_display})"
        return full_name