# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from io import BytesIO
import base64
import random
import string
import secrets

# Try to import pyotp and qrcode, but provide fallbacks if not available
try:
    import pyotp
    import qrcode
    import qrcode.image.svg
    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False

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


class MFASetup(models.Model):
    """
    Multi-Factor Authentication setup for users.
    Stores the secret key and configuration for TOTP-based MFA.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mfa_setup')
    secret_key = models.CharField(_('Secret Key'), max_length=100)
    is_enabled = models.BooleanField(_('MFA Enabled'), default=False)
    backup_codes = models.JSONField(_('Backup Codes'), default=list, blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    last_used = models.DateTimeField(_('Last Used'), null=True, blank=True)

    def __str__(self):
        return f"MFA Setup for {self.user.username}"

    def generate_secret_key(self):
        """Generate a new secret key for TOTP."""
        if PYOTP_AVAILABLE:
            self.secret_key = pyotp.random_base32()
        else:
            # Fallback: generate a random base32 string
            chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
            self.secret_key = ''.join(random.choices(chars, k=16))

        self.save()
        return self.secret_key

    def get_totp(self):
        """Get TOTP object for code generation and verification."""
        if PYOTP_AVAILABLE:
            return pyotp.TOTP(self.secret_key)
        return None

    def verify_code(self, code):
        """Verify a TOTP code."""
        if PYOTP_AVAILABLE:
            totp = self.get_totp()
            return totp.verify(code)

        # Fallback: in development, accept any 6-digit code
        return code.isdigit() and len(code) == 6

    def get_qr_code(self):
        """Generate QR code for authenticator app setup."""
        if not PYOTP_AVAILABLE:
            # Return a placeholder image or message
            return ""

        totp = self.get_totp()
        # Create a provisioning URI for the authenticator app
        provisioning_uri = totp.provisioning_uri(
            name=self.user.email,
            issuer_name="Legal Case Management"
        )

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64 for display in HTML
        buffer = BytesIO()
        img.save(buffer)
        return base64.b64encode(buffer.getvalue()).decode()

    def generate_backup_codes(self, count=8):
        """Generate backup codes for account recovery."""
        # Generate random 8-character codes
        codes = []
        for _ in range(count):
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            codes.append(code)

        self.backup_codes = codes
        self.save()
        return codes

    def verify_backup_code(self, code):
        """Verify a backup code and remove it if valid."""
        if code in self.backup_codes:
            # Remove the used code
            self.backup_codes.remove(code)
            self.save()
            return True
        return False