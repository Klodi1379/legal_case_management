"""
Core models for the legal case management system.

This module defines core models used across the application, including
audit logging and system-wide settings.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import json

class AuditLog(models.Model):
    """
    Comprehensive audit logging for compliance and security.

    Tracks all significant actions in the system for compliance
    with legal and regulatory requirements.
    """
    ACTION_CHOICES = (
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('EXPORT', 'Export'),
        ('SHARE', 'Share'),
        ('OTHER', 'Other'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('User')
    )
    action = models.CharField(_('Action'), max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_('IP Address'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)

    # For linking to any model
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name=_('Content Type')
    )
    object_id = models.CharField(_('Object ID'), max_length=255, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # Additional details
    object_repr = models.CharField(_('Object Representation'), max_length=255, blank=True)
    changes = models.JSONField(_('Changes'), null=True, blank=True)
    additional_data = models.JSONField(_('Additional Data'), null=True, blank=True)

    class Meta:
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        if self.user:
            user_str = self.user.get_full_name() or self.user.username
        else:
            user_str = 'System'

        return f"{user_str} - {self.get_action_display()} - {self.timestamp}"

    @classmethod
    def log(cls, user, action, obj=None, changes=None, ip_address=None, user_agent=None, additional_data=None):
        """
        Create an audit log entry.

        Args:
            user: The user performing the action
            action: The action being performed (one of ACTION_CHOICES)
            obj: The object being acted upon (optional)
            changes: Dictionary of changes made (optional)
            ip_address: IP address of the user (optional)
            user_agent: User agent string (optional)
            additional_data: Any additional data to log (optional)

        Returns:
            The created AuditLog instance
        """
        log_entry = cls(
            user=user,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            changes=changes,
            additional_data=additional_data
        )

        if obj:
            log_entry.content_type = ContentType.objects.get_for_model(obj)
            log_entry.object_id = str(obj.pk)
            log_entry.object_repr = str(obj)

        log_entry.save()
        return log_entry


class SystemSetting(models.Model):
    """
    System-wide settings for the application.

    Stores configuration settings that can be changed through the admin
    interface without requiring code changes.
    """
    key = models.CharField(_('Key'), max_length=100, unique=True)
    value = models.TextField(_('Value'))
    value_type = models.CharField(
        _('Value Type'),
        max_length=20,
        choices=(
            ('string', 'String'),
            ('integer', 'Integer'),
            ('float', 'Float'),
            ('boolean', 'Boolean'),
            ('json', 'JSON'),
        ),
        default='string'
    )
    description = models.TextField(_('Description'), blank=True)
    category = models.CharField(_('Category'), max_length=100, default='general')
    is_public = models.BooleanField(
        _('Public'),
        default=False,
        help_text=_('Whether this setting is visible to non-admin users')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('System Setting')
        verbose_name_plural = _('System Settings')
        ordering = ['category', 'key']

    def __str__(self):
        return f"{self.key} ({self.category})"

    @property
    def typed_value(self):
        """
        Return the value converted to its proper type.
        """
        if self.value_type == 'integer':
            return int(self.value)
        elif self.value_type == 'float':
            return float(self.value)
        elif self.value_type == 'boolean':
            return self.value.lower() in ('true', 'yes', '1', 'on')
        elif self.value_type == 'json':
            try:
                return json.loads(self.value)
            except json.JSONDecodeError:
                return None
        else:
            return self.value

    @classmethod
    def get(cls, key, default=None):
        """
        Get a setting value by key.

        Args:
            key: The setting key
            default: Default value if setting not found

        Returns:
            The setting value converted to its proper type
        """
        try:
            setting = cls.objects.get(key=key)
            return setting.typed_value
        except cls.DoesNotExist:
            return default
