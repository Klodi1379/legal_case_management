"""
Custom exceptions for AI services.

This module defines custom exceptions for AI services to provide
more specific error handling and better diagnostics.
"""

class AIServiceException(Exception):
    """Base exception for all AI service errors."""
    pass


class ServiceConnectionError(AIServiceException):
    """Exception raised when a connection to an AI service fails."""
    
    def __init__(self, service_name, endpoint, message=None, original_exception=None):
        self.service_name = service_name
        self.endpoint = endpoint
        self.original_exception = original_exception
        msg = f"Failed to connect to {service_name} at {endpoint}"
        if message:
            msg += f": {message}"
        super().__init__(msg)


class ServiceTimeoutError(ServiceConnectionError):
    """Exception raised when a connection to an AI service times out."""
    
    def __init__(self, service_name, endpoint, timeout, original_exception=None):
        self.timeout = timeout
        message = f"Connection timed out after {timeout} seconds"
        super().__init__(service_name, endpoint, message, original_exception)


class ServiceResponseError(AIServiceException):
    """Exception raised when an AI service returns an error response."""
    
    def __init__(self, service_name, status_code=None, response_text=None, original_exception=None):
        self.service_name = service_name
        self.status_code = status_code
        self.response_text = response_text
        self.original_exception = original_exception
        
        msg = f"Error response from {service_name}"
        if status_code:
            msg += f" (Status code: {status_code})"
        if response_text:
            msg += f": {response_text}"
        super().__init__(msg)


class ServiceParsingError(AIServiceException):
    """Exception raised when parsing the response from an AI service fails."""
    
    def __init__(self, service_name, message=None, original_exception=None):
        self.service_name = service_name
        self.original_exception = original_exception
        
        msg = f"Failed to parse response from {service_name}"
        if message:
            msg += f": {message}"
        super().__init__(msg)


class ModelNotFoundError(AIServiceException):
    """Exception raised when a requested model is not found."""
    
    def __init__(self, model_name):
        self.model_name = model_name
        super().__init__(f"Model not found: {model_name}")


class ServiceNotAvailableError(AIServiceException):
    """Exception raised when a service is not available."""
    
    def __init__(self, service_name, reason=None):
        self.service_name = service_name
        msg = f"Service not available: {service_name}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg)
