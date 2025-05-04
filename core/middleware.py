"""
Middleware for the legal case management system.

This module provides middleware components for features like
audit logging and security.
"""

import json
import logging
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from .models import AuditLog

logger = logging.getLogger(__name__)

class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log user actions for audit purposes.

    This middleware logs significant actions like login, logout, and
    data modifications to maintain a comprehensive audit trail.
    """

    AUDIT_PATHS = [
        # Authentication
        ('/accounts/login/', 'LOGIN'),
        ('/accounts/logout/', 'LOGOUT'),

        # Case actions
        ('/cases/create/', 'CREATE'),
        ('/cases/*/update/', 'UPDATE'),

        # Document actions
        ('/documents/upload/', 'CREATE'),
        ('/documents/delete/*', 'DELETE'),

        # Client actions - sensitive data
        ('/clients/create/', 'CREATE'),
        ('/clients/*/update/', 'UPDATE'),
        ('/clients/*/detail/', 'VIEW'),

        # MFA actions
        ('/accounts/mfa/setup/', 'UPDATE'),
        ('/accounts/mfa/disable/', 'UPDATE'),
        ('/accounts/mfa/backup-codes/', 'VIEW'),
        ('/accounts/mfa/verify/', 'VIEW'),
    ]

    EXEMPT_PATHS = [
        '/static/',
        '/media/',
        '/favicon.ico',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Process the view and log relevant actions."""
        # Skip exempt paths
        if any(request.path.startswith(path) for path in self.EXEMPT_PATHS):
            return None

        # Skip if user is not authenticated
        if isinstance(request.user, AnonymousUser):
            return None

        # Determine action type based on path and method
        action = self._get_action(request)
        if not action:
            return None

        # Log the action
        try:
            # Get IP address
            ip_address = self._get_client_ip(request)

            # Get user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            # Additional data
            additional_data = {
                'method': request.method,
                'path': request.path,
                'query_params': dict(request.GET.items()),
            }

            # Create log entry
            AuditLog.log(
                user=request.user,
                action=action,
                ip_address=ip_address,
                user_agent=user_agent,
                additional_data=additional_data
            )

        except Exception as e:
            logger.error(f"Error in AuditLogMiddleware: {str(e)}")

        return None

    def _get_action(self, request):
        """Determine the action type based on the request."""
        # Check for specific paths
        for path, action in self.AUDIT_PATHS:
            if self._path_matches(request.path, path):
                return action

        # Default actions based on HTTP method
        if request.method == 'POST':
            return 'CREATE'
        elif request.method in ('PUT', 'PATCH'):
            return 'UPDATE'
        elif request.method == 'DELETE':
            return 'DELETE'

        # For GET requests to specific resources (not list views)
        if request.method == 'GET' and any(segment.isdigit() for segment in request.path.split('/')):
            return 'VIEW'

        return None

    def _path_matches(self, actual_path, pattern):
        """Check if a path matches a pattern with wildcards."""
        if '*' not in pattern:
            return actual_path == pattern

        parts = pattern.split('/')
        actual_parts = actual_path.split('/')

        if len(parts) != len(actual_parts):
            return False

        for i, part in enumerate(parts):
            if part == '*':
                continue
            if part != actual_parts[i]:
                return False

        return True

    def _get_client_ip(self, request):
        """Get the client IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
