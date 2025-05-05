"""
Audit logging utilities for tracking user actions.
"""
import json
from typing import Any, Dict, Optional
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from core.utils.logging import StructuredLogger


User = get_user_model()
logger = StructuredLogger(__name__)


class AuditLogManager:
    """
    Manager for creating audit log entries.
    """
    
    @staticmethod
    def log_action(
        user: User,
        action: str,
        model_name: str,
        object_id: Any,
        changes: Optional[Dict[str, Any]] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """
        Create an audit log entry for a user action.
        
        Args:
            user: User who performed the action
            action: Action performed (create, update, delete, etc.)
            model_name: Name of the model affected
            object_id: ID of the object affected
            changes: Dictionary of field changes
            extra_data: Additional data to log
        """
        from core.models import AuditLog  # Import here to avoid circular imports
        
        audit_log = AuditLog.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=str(object_id),
            changes_json=json.dumps(changes) if changes else None,
            extra_data=json.dumps(extra_data) if extra_data else None,
            ip_address=extra_data.get('ip_address') if extra_data else None,
            user_agent=extra_data.get('user_agent') if extra_data else None
        )
        
        logger.info(
            "Audit log created",
            audit_log_id=audit_log.id,
            user_id=user.id,
            action=action,
            model_name=model_name,
            object_id=object_id
        )
        
        return audit_log


def audit_action(action: str, model_name: str):
    """
    Decorator for auditing model actions.
    
    Args:
        action: Action being performed
        model_name: Name of the model
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # Get the object ID before the action (for delete operations)
            object_id = self.pk if hasattr(self, 'pk') else None
            
            # Store the original state for update operations
            original_state = None
            if action == 'update' and object_id:
                original_state = {
                    field.name: getattr(self, field.name)
                    for field in self._meta.fields
                    if not field.name.startswith('_')
                }
            
            # Perform the action
            result = func(self, *args, **kwargs)
            
            # Get the user from the request if available
            user = None
            request = kwargs.get('request')
            if request and hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user
            
            # If no user in kwargs, try to get it from created_by or updated_by
            if not user and hasattr(self, 'created_by'):
                user = self.created_by
            
            if user:
                # Calculate changes for update operations
                changes = None
                if action == 'update' and original_state:
                    changes = {}
                    for field_name, old_value in original_state.items():
                        new_value = getattr(self, field_name)
                        if old_value != new_value:
                            changes[field_name] = {
                                'old': str(old_value),
                                'new': str(new_value)
                            }
                
                # Create audit log
                AuditLogManager.log_action(
                    user=user,
                    action=action,
                    model_name=model_name,
                    object_id=object_id or self.pk,
                    changes=changes
                )
            
            return result
        
        return wrapper
    return decorator


def get_model_changes(instance: models.Model, old_instance: models.Model) -> Dict[str, Any]:
    """
    Compare two model instances and return the changes.
    
    Args:
        instance: New instance
        old_instance: Old instance
        
    Returns:
        Dictionary of changed fields with old and new values
    """
    changes = {}
    
    for field in instance._meta.fields:
        field_name = field.name
        
        # Skip auto fields and hidden fields
        if field_name.startswith('_') or field.auto_created:
            continue
        
        old_value = getattr(old_instance, field_name)
        new_value = getattr(instance, field_name)
        
        if old_value != new_value:
            changes[field_name] = {
                'old': str(old_value),
                'new': str(new_value)
            }
    
    return changes


def audit_login(user: User, success: bool, ip_address: str = None, user_agent: str = None):
    """
    Log user login attempt.
    
    Args:
        user: User attempting to login
        success: Whether login was successful
        ip_address: IP address of the request
        user_agent: User agent string
    """
    action = 'login_success' if success else 'login_failed'
    
    AuditLogManager.log_action(
        user=user,
        action=action,
        model_name='User',
        object_id=user.id,
        extra_data={
            'ip_address': ip_address,
            'user_agent': user_agent,
            'success': success
        }
    )


def audit_logout(user: User, ip_address: str = None, user_agent: str = None):
    """
    Log user logout.
    
    Args:
        user: User logging out
        ip_address: IP address of the request
        user_agent: User agent string
    """
    AuditLogManager.log_action(
        user=user,
        action='logout',
        model_name='User',
        object_id=user.id,
        extra_data={
            'ip_address': ip_address,
            'user_agent': user_agent
        }
    )
