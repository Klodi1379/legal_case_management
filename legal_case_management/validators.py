"""
Custom password validators for the legal case management system.
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class UppercasePasswordValidator:
    """
    Validates that the password contains at least one uppercase letter.
    """
    def validate(self, password, user=None):
        if not any(char.isupper() for char in password):
            raise ValidationError(
                _("This password must contain at least one uppercase letter."),
                code='password_no_upper',
            )

    def get_help_text(self):
        return _("Your password must contain at least one uppercase letter.")


class LowercasePasswordValidator:
    """
    Validates that the password contains at least one lowercase letter.
    """
    def validate(self, password, user=None):
        if not any(char.islower() for char in password):
            raise ValidationError(
                _("This password must contain at least one lowercase letter."),
                code='password_no_lower',
            )

    def get_help_text(self):
        return _("Your password must contain at least one lowercase letter.")


class SpecialCharacterPasswordValidator:
    """
    Validates that the password contains at least one special character.
    """
    def validate(self, password, user=None):
        special_characters = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(char in special_characters for char in password):
            raise ValidationError(
                _("This password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)."),
                code='password_no_special',
            )

    def get_help_text(self):
        return _("Your password must contain at least one special character.")
