"""
Structured logging utilities for the legal case management system.
"""
import logging
import json
import time
from functools import wraps
from typing import Dict, Any, Callable
from django.utils import timezone


class StructuredLogger:
    """
    Structured logging implementation for better log analysis.
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _format_log_data(self, level: str, message: str, **kwargs) -> Dict[str, Any]:
        """Format log data with consistent structure."""
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'level': level,
            'message': message,
            'logger': self.logger.name,
        }
        
        # Add any additional context
        if kwargs:
            log_data['context'] = kwargs
        
        return log_data
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data."""
        log_data = self._format_log_data('DEBUG', message, **kwargs)
        self.logger.debug(json.dumps(log_data))
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data."""
        log_data = self._format_log_data('INFO', message, **kwargs)
        self.logger.info(json.dumps(log_data))
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data."""
        log_data = self._format_log_data('WARNING', message, **kwargs)
        self.logger.warning(json.dumps(log_data))
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data."""
        log_data = self._format_log_data('ERROR', message, **kwargs)
        self.logger.error(json.dumps(log_data))
    
    def critical(self, message: str, **kwargs):
        """Log critical message with structured data."""
        log_data = self._format_log_data('CRITICAL', message, **kwargs)
        self.logger.critical(json.dumps(log_data))


def log_execution_time(logger_name: str = None):
    """
    Decorator to log function execution time.
    
    Args:
        logger_name: Name of the logger to use. If None, uses the module name.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = StructuredLogger(logger_name or func.__module__)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.info(
                    f"Function executed successfully",
                    function_name=func.__name__,
                    execution_time=f"{execution_time:.3f}s"
                )
                
                return result
            
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Function failed with error",
                    function_name=func.__name__,
                    execution_time=f"{execution_time:.3f}s",
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
        
        return wrapper
    return decorator


def log_database_operations(logger_name: str = 'database'):
    """
    Decorator to log database operations.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = StructuredLogger(logger_name)
            
            # Extract model name if available
            model_name = None
            if hasattr(args[0], '__class__'):
                model_name = args[0].__class__.__name__
            
            try:
                result = func(*args, **kwargs)
                
                logger.info(
                    "Database operation successful",
                    operation=func.__name__,
                    model=model_name
                )
                
                return result
            
            except Exception as e:
                logger.error(
                    "Database operation failed",
                    operation=func.__name__,
                    model=model_name,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
        
        return wrapper
    return decorator


def log_security_event(event_type: str, logger_name: str = 'security'):
    """
    Decorator to log security-related events.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = StructuredLogger(logger_name)
            
            # Extract user information if available
            user_info = {}
            if hasattr(args[0], 'user'):
                user = args[0].user
                if user.is_authenticated:
                    user_info = {
                        'user_id': user.id,
                        'username': user.username,
                        'email': user.email
                    }
            
            try:
                result = func(*args, **kwargs)
                
                logger.info(
                    f"Security event: {event_type}",
                    event_type=event_type,
                    function=func.__name__,
                    **user_info
                )
                
                return result
            
            except Exception as e:
                logger.warning(
                    f"Security event failed: {event_type}",
                    event_type=event_type,
                    function=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__,
                    **user_info
                )
                raise
        
        return wrapper
    return decorator
