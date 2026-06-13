class OMNISEEKException(Exception):
    """Base exception class for all system errors."""

class DatabaseError(OMNISEEKException):
    """Exception raised for database operational failures."""

class NotFoundError(OMNISEEKException):
    """Exception raised when a requested resource is absent."""

class ValidationError(OMNISEEKException):
    """Exception raised when model validation validation fails."""
