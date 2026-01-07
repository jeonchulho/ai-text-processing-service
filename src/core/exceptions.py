"""
Custom exception classes for the application.

This module defines custom exceptions used throughout the application
for better error handling and API responses.
"""

from typing import Any, Optional


class AITextProcessingException(Exception):
    """Base exception class for the application."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Any] = None
    ):
        """
        Initialize the exception.

        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class TranslationError(AITextProcessingException):
    """Exception raised when translation fails."""

    def __init__(self, message: str = "Translation failed", details: Optional[Any] = None):
        super().__init__(message, status_code=422, details=details)


class SummarizationError(AITextProcessingException):
    """Exception raised when summarization fails."""

    def __init__(self, message: str = "Summarization failed", details: Optional[Any] = None):
        super().__init__(message, status_code=422, details=details)


class ScheduleDetectionError(AITextProcessingException):
    """Exception raised when schedule detection fails."""

    def __init__(self, message: str = "Schedule detection failed", details: Optional[Any] = None):
        super().__init__(message, status_code=422, details=details)


class DatabaseError(AITextProcessingException):
    """Exception raised when database operation fails."""

    def __init__(self, message: str = "Database operation failed", details: Optional[Any] = None):
        super().__init__(message, status_code=500, details=details)


class CacheError(AITextProcessingException):
    """Exception raised when cache operation fails."""

    def __init__(self, message: str = "Cache operation failed", details: Optional[Any] = None):
        super().__init__(message, status_code=500, details=details)


class VectorStoreError(AITextProcessingException):
    """Exception raised when vector store operation fails."""

    def __init__(self, message: str = "Vector store operation failed", details: Optional[Any] = None):
        super().__init__(message, status_code=500, details=details)


class LLMError(AITextProcessingException):
    """Exception raised when LLM operation fails."""

    def __init__(self, message: str = "LLM operation failed", details: Optional[Any] = None):
        super().__init__(message, status_code=502, details=details)


class ValidationError(AITextProcessingException):
    """Exception raised when input validation fails."""

    def __init__(self, message: str = "Validation failed", details: Optional[Any] = None):
        super().__init__(message, status_code=400, details=details)


class NotFoundError(AITextProcessingException):
    """Exception raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(message, status_code=404, details=details)


class AuthenticationError(AITextProcessingException):
    """Exception raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", details: Optional[Any] = None):
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(AITextProcessingException):
    """Exception raised when authorization fails."""

    def __init__(self, message: str = "Authorization failed", details: Optional[Any] = None):
        super().__init__(message, status_code=403, details=details)


class RateLimitError(AITextProcessingException):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Any] = None):
        super().__init__(message, status_code=429, details=details)
