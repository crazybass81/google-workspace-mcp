"""Common Pydantic models for Google Workspace MCP tools."""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from .response_formatter import ResponseFormat


class BaseMCPInput(BaseModel):
    """Base model for all MCP tool inputs with common configuration."""

    model_config = ConfigDict(
        str_strip_whitespace=True,  # Auto-strip whitespace from strings
        validate_assignment=True,    # Validate on assignment
        extra='forbid',              # Forbid extra fields
        use_enum_values=True         # Use enum values instead of enum objects
    )


class BaseListInput(BaseMCPInput):
    """Base model for list/search operations with pagination."""

    limit: int = Field(
        default=20,
        description="Maximum number of results to return (1-1000)",
        ge=1,
        le=1000
    )
    offset: int = Field(
        default=0,
        description="Number of results to skip for pagination",
        ge=0
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class FileIdInput(BaseMCPInput):
    """Base model for operations requiring a file ID."""

    file_id: str = Field(
        ...,
        description="Google Drive/Docs/Sheets/Slides file ID (e.g., '1A2B3C4D5E6F7G8H9I0J')",
        min_length=1,
        max_length=200,
        pattern=r'^[a-zA-Z0-9_-]+$'
    )

    @field_validator('file_id')
    @classmethod
    def validate_file_id(cls, v: str) -> str:
        """Validate file ID format."""
        if not v.strip():
            raise ValueError("File ID cannot be empty")
        return v.strip()


class DocumentIdInput(FileIdInput):
    """Base model for Google Docs operations."""

    document_id: str = Field(
        ...,
        description="Google Docs document ID (e.g., '1A2B3C4D5E6F7G8H9I0J')",
        min_length=1,
        max_length=200,
        pattern=r'^[a-zA-Z0-9_-]+$'
    )

    @field_validator('document_id')
    @classmethod
    def validate_document_id(cls, v: str) -> str:
        """Validate document ID format."""
        if not v.strip():
            raise ValueError("Document ID cannot be empty")
        return v.strip()


class SpreadsheetIdInput(BaseMCPInput):
    """Base model for Google Sheets operations."""

    spreadsheet_id: str = Field(
        ...,
        description="Google Sheets spreadsheet ID (e.g., '1A2B3C4D5E6F7G8H9I0J')",
        min_length=1,
        max_length=200,
        pattern=r'^[a-zA-Z0-9_-]+$'
    )

    @field_validator('spreadsheet_id')
    @classmethod
    def validate_spreadsheet_id(cls, v: str) -> str:
        """Validate spreadsheet ID format."""
        if not v.strip():
            raise ValueError("Spreadsheet ID cannot be empty")
        return v.strip()


class PresentationIdInput(BaseMCPInput):
    """Base model for Google Slides operations."""

    presentation_id: str = Field(
        ...,
        description="Google Slides presentation ID (e.g., '1A2B3C4D5E6F7G8H9I0J')",
        min_length=1,
        max_length=200,
        pattern=r'^[a-zA-Z0-9_-]+$'
    )

    @field_validator('presentation_id')
    @classmethod
    def validate_presentation_id(cls, v: str) -> str:
        """Validate presentation ID format."""
        if not v.strip():
            raise ValueError("Presentation ID cannot be empty")
        return v.strip()


class MessageIdInput(BaseMCPInput):
    """Base model for Gmail message operations."""

    message_id: str = Field(
        ...,
        description="Gmail message ID (e.g., '18a1b2c3d4e5f6g7')",
        min_length=1,
        max_length=200
    )

    @field_validator('message_id')
    @classmethod
    def validate_message_id(cls, v: str) -> str:
        """Validate message ID format."""
        if not v.strip():
            raise ValueError("Message ID cannot be empty")
        return v.strip()
