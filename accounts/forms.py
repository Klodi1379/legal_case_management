# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, MFASetup

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'is_client', 'is_lawyer']

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'address']


class MFASetupForm(forms.Form):
    """Form for setting up MFA."""
    enable_mfa = forms.BooleanField(
        required=False,
        label="Enable Two-Factor Authentication",
        help_text="Enhance your account security with two-factor authentication."
    )


class MFAVerificationForm(forms.Form):
    """Form for verifying MFA code."""
    verification_code = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        label="Verification Code",
        help_text="Enter the 6-digit code from your authenticator app.",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123456',
            'autocomplete': 'off',
            'autofocus': 'autofocus'
        })
    )


class MFABackupCodeForm(forms.Form):
    """Form for using backup codes."""
    backup_code = forms.CharField(
        max_length=8,
        min_length=8,
        required=True,
        label="Backup Code",
        help_text="Enter one of your backup codes.",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ABC12345',
            'autocomplete': 'off',
            'autofocus': 'autofocus'
        })
    )