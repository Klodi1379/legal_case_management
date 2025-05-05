"""
Custom exceptions for the legal case management system.
"""


class LegalCaseException(Exception):
    """Base exception for all legal case management errors."""
    pass


class AIServiceException(LegalCaseException):
    """Raised when AI service encounters an error."""
    pass


class DocumentProcessingException(LegalCaseException):
    """Raised when document processing fails."""
    pass


class ConflictCheckException(LegalCaseException):
    """Raised when conflict check fails."""
    pass


class BillingException(LegalCaseException):
    """Raised when billing operation fails."""
    pass


class SecurityException(LegalCaseException):
    """Raised when security check fails."""
    pass


class ValidationException(LegalCaseException):
    """Raised when data validation fails."""
    pass


class PermissionDeniedException(LegalCaseException):
    """Raised when user lacks required permissions."""
    pass
