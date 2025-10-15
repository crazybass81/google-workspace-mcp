"""Error handling utilities for Google Workspace MCP Server."""

from typing import Any, Dict, Optional
from google.api_core import exceptions as google_exceptions
from .logger import setup_logger

logger = setup_logger(__name__)


class GoogleWorkspaceError(Exception):
    """Base exception for Google Workspace MCP operations."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.original_error = original_error

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        return {
            "error": {
                "type": self.__class__.__name__,
                "message": self.message,
                "details": self.details
            }
        }


class AuthenticationError(GoogleWorkspaceError):
    """Raised when authentication fails."""
    pass


class PermissionError(GoogleWorkspaceError):
    """Raised when user lacks necessary permissions."""
    pass


class ResourceNotFoundError(GoogleWorkspaceError):
    """Raised when requested resource doesn't exist."""
    pass


class RateLimitError(GoogleWorkspaceError):
    """Raised when API rate limit is exceeded."""
    pass


class InvalidRequestError(GoogleWorkspaceError):
    """Raised when request parameters are invalid."""
    pass


def handle_google_api_error(error: Exception) -> GoogleWorkspaceError:
    """Convert Google API exceptions to custom exceptions.

    Args:
        error: Original Google API exception

    Returns:
        Appropriate GoogleWorkspaceError subclass
    """
    if isinstance(error, google_exceptions.Unauthenticated):
        return AuthenticationError(
            "Authentication failed. Please check your credentials.",
            original_error=error
        )

    if isinstance(error, google_exceptions.PermissionDenied):
        return PermissionError(
            "Permission denied. Check your account permissions.",
            original_error=error
        )

    if isinstance(error, google_exceptions.NotFound):
        return ResourceNotFoundError(
            "Requested resource not found.",
            original_error=error
        )

    if isinstance(error, google_exceptions.ResourceExhausted):
        return RateLimitError(
            "API rate limit exceeded. Please try again later.",
            details={"retry_after": 60},
            original_error=error
        )

    if isinstance(error, google_exceptions.InvalidArgument):
        return InvalidRequestError(
            "Invalid request parameters.",
            original_error=error
        )

    # Generic error for unexpected exceptions
    logger.error(f"Unhandled Google API error: {error}")
    return GoogleWorkspaceError(
        "An unexpected error occurred.",
        details={"original_error": str(error)},
        original_error=error
    )


def with_error_handling(func):
    """Decorator for consistent error handling.

    Args:
        func: Async function to wrap

    Returns:
        Wrapped function with error handling
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except GoogleWorkspaceError:
            # Re-raise custom errors as-is
            raise
        except google_exceptions.GoogleAPICallError as e:
            # Convert Google API errors
            raise handle_google_api_error(e)
        except Exception as e:
            # Log and convert unexpected errors
            logger.exception(f"Unexpected error in {func.__name__}")
            raise GoogleWorkspaceError(
                f"Unexpected error in {func.__name__}",
                details={"error": str(e)},
                original_error=e
            )

    return wrapper
