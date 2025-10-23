"""MCP tools for Google Drive operations using FastMCP."""

import json
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from ..server_fastmcp import mcp
from ..services.drive_service import DriveService
from ..utils.logger import setup_logger
from ..utils.base_models import BaseMCPInput, BaseListInput, FileIdInput
from ..utils.response_formatter import (
    ResponseFormat,
    format_file_list,
    format_pagination_metadata,
    format_error,
    create_success_response,
    CHARACTER_LIMIT
)

logger = setup_logger(__name__)
drive_service = DriveService()


# ============================================================================
# Pydantic Input Models
# ============================================================================

class DriveSearchInput(BaseListInput):
    """Input model for searching files in Google Drive."""

    query: Optional[str] = Field(
        default=None,
        description="Search query for file name (e.g., 'budget report', 'Q1 analysis', '*.pdf')",
        max_length=500
    )
    folder_id: Optional[str] = Field(
        default=None,
        description="Limit search to specific folder ID (e.g., '1A2B3C4D5E6F')",
        pattern=r'^[a-zA-Z0-9_-]+$'
    )
    file_type: Optional[str] = Field(
        default=None,
        description="Filter by MIME type (e.g., 'application/pdf', 'image/jpeg', 'application/vnd.google-apps.document')"
    )


class DriveReadFileInput(BaseMCPInput):
    """Input model for reading file content."""

    file_id: str = Field(
        ...,
        description="Google Drive file ID (e.g., '1A2B3C4D5E6F7G8H9I0J')",
        min_length=1,
        pattern=r'^[a-zA-Z0-9_-]+$'
    )
    mime_type: Optional[str] = Field(
        default=None,
        description="Export MIME type for Google Docs/Sheets/Slides (e.g., 'text/plain', 'application/pdf', 'text/html')"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class DriveCreateFileInput(BaseMCPInput):
    """Input model for creating a new file."""

    name: str = Field(
        ...,
        description="File name (e.g., 'report.txt', 'notes.md')",
        min_length=1,
        max_length=255
    )
    content: str = Field(
        default="",
        description="File content (text)",
        max_length=1000000  # 1MB limit for text content
    )
    mime_type: str = Field(
        default="text/plain",
        description="MIME type (e.g., 'text/plain', 'text/markdown', 'text/html')"
    )
    folder_id: Optional[str] = Field(
        default=None,
        description="Parent folder ID to create file in (optional)",
        pattern=r'^[a-zA-Z0-9_-]+$'
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format for response"
    )


class DriveUpdateFileInput(BaseMCPInput):
    """Input model for updating an existing file."""

    file_id: str = Field(
        ...,
        description="Google Drive file ID to update",
        pattern=r'^[a-zA-Z0-9_-]+$'
    )
    content: Optional[str] = Field(
        default=None,
        description="New file content (if updating content)",
        max_length=1000000
    )
    name: Optional[str] = Field(
        default=None,
        description="New file name (if renaming)",
        max_length=255
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format for response"
    )


class DriveDeleteFileInput(FileIdInput):
    """Input model for deleting a file."""
    pass


class DriveUploadFileInput(BaseMCPInput):
    """Input model for uploading a local file."""

    local_path: str = Field(
        ...,
        description="Local file path to upload (e.g., '/path/to/document.pdf', './report.xlsx')",
        min_length=1
    )
    name: Optional[str] = Field(
        default=None,
        description="Name for uploaded file (optional, defaults to filename from path)",
        max_length=255
    )
    folder_id: Optional[str] = Field(
        default=None,
        description="Parent folder ID to upload to (optional)",
        pattern=r'^[a-zA-Z0-9_-]+$'
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format for response"
    )


class DriveDownloadFileInput(BaseMCPInput):
    """Input model for downloading a file."""

    file_id: str = Field(
        ...,
        description="Google Drive file ID to download",
        pattern=r'^[a-zA-Z0-9_-]+$'
    )
    local_path: str = Field(
        ...,
        description="Local path to save downloaded file (e.g., '/path/to/save/file.pdf')",
        min_length=1
    )
    mime_type: Optional[str] = Field(
        default=None,
        description="Export MIME type for Google Docs files (e.g., 'application/pdf', 'text/plain')"
    )


class DriveListSharedDrivesInput(BaseListInput):
    """Input model for listing shared drives."""
    pass


# ============================================================================
# Tool Implementations
# ============================================================================

@mcp.tool(
    name="drive_search_files",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def drive_search_files(params: DriveSearchInput) -> str:
    """Search for files and folders in Google Drive with flexible filtering.

    This tool searches across all accessible Google Drive files and folders using
    query-based matching. It supports filtering by folder, MIME type, and includes
    pagination for large result sets. Results include file metadata (name, ID, type,
    modified date, and web link).

    Use this when you need to:
    - Find specific files by name or pattern
    - Explore folder contents
    - Discover documents by MIME type
    - List files matching certain criteria

    Args:
        params (DriveSearchInput): Validated search parameters with:
            - query: Optional search query for file name matching
            - folder_id: Optional folder ID to limit search scope
            - file_type: Optional MIME type filter
            - limit: Maximum results per page (1-1000, default 20)
            - offset: Pagination offset (default 0)
            - response_format: Output format (markdown/json)

    Returns:
        str: Formatted search results with pagination metadata

    Examples:
        - Find PDFs: file_type='application/pdf'
        - Search in folder: folder_id='1A2B3C', query='report'
        - Limit results: limit=10, offset=0
    """
    try:
        # Call drive service with validated parameters
        result = await drive_service.search_files(
            query=params.query,
            folder_id=params.folder_id,
            file_type=params.file_type,
            max_results=params.limit
        )

        if not result:
            return "No files found matching the search criteria."

        # Apply offset for pagination
        total_count = len(result)
        paginated_result = result[params.offset:params.offset + params.limit]
        has_more = (params.offset + params.limit) < total_count

        # Format response
        if params.response_format == ResponseFormat.JSON:
            pagination = format_pagination_metadata(
                total=total_count,
                count=len(paginated_result),
                offset=params.offset,
                has_more=has_more,
                next_offset=params.offset + params.limit if has_more else None
            )
            response = {
                "files": paginated_result,
                "pagination": pagination
            }
            return json.dumps(response, indent=2)

        # Markdown format
        response_text = format_file_list(paginated_result, ResponseFormat.MARKDOWN)

        # Add pagination info
        if total_count > params.limit:
            response_text += f"\n\n📄 **Pagination**: Showing {len(paginated_result)} of {total_count} results"
            if has_more:
                response_text += f" (use offset={params.offset + params.limit} for more)"

        return response_text

    except Exception as e:
        logger.error(f"drive_search_files error: {str(e)}")
        return format_error(e, "searching files")


@mcp.tool(
    name="drive_read_file",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def drive_read_file(params: DriveReadFileInput) -> str:
    """Read file content from Google Drive.

    Retrieves the content of a file from Google Drive. For Google Docs, Sheets,
    and Slides, you can specify an export MIME type to convert the file to a
    different format (e.g., PDF, plain text, HTML).

    Use this when you need to:
    - Read text file contents
    - Export Google Docs/Sheets/Slides to different formats
    - Access file metadata and content together

    Args:
        params (DriveReadFileInput): Validated parameters with:
            - file_id: Google Drive file ID
            - mime_type: Optional export MIME type for Google Workspace files
            - response_format: Output format (markdown/json)

    Returns:
        str: File content with metadata

    Examples:
        - Read text file: file_id='1A2B3C'
        - Export Doc as PDF: file_id='1A2B3C', mime_type='application/pdf'
        - Export Doc as text: file_id='1A2B3C', mime_type='text/plain'
    """
    try:
        result = await drive_service.read_file(
            file_id=params.file_id,
            mime_type=params.mime_type
        )

        metadata = result.get('metadata', {})
        content = result.get('content', '')

        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "metadata": metadata,
                "content": content,
                "content_length": len(content)
            }, indent=2)

        # Markdown format
        response = f"# File: {metadata.get('name', 'Unknown')}\n\n"
        response += f"- **ID**: `{metadata.get('id', 'N/A')}`\n"
        response += f"- **Type**: {metadata.get('mimeType', 'unknown')}\n"
        response += f"- **Modified**: {metadata.get('modifiedTime', 'N/A')}\n"
        if metadata.get('webViewLink'):
            response += f"- **Link**: {metadata['webViewLink']}\n"
        response += f"\n## Content\n\n{content}"

        # Check character limit
        if len(response) > CHARACTER_LIMIT:
            truncated = response[:CHARACTER_LIMIT - 200]
            truncated += "\n\n⚠️ **Content Truncated**: File content exceeds character limit. Consider downloading the file instead."
            return truncated

        return response

    except Exception as e:
        logger.error(f"drive_read_file error: {str(e)}")
        return format_error(e, "reading file")


@mcp.tool(
    name="drive_create_file",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def drive_create_file(params: DriveCreateFileInput) -> str:
    """Create a new file in Google Drive.

    Creates a new file with the specified name and content. You can optionally
    place it in a specific folder and set the MIME type.

    Args:
        params (DriveCreateFileInput): File creation parameters

    Returns:
        str: Success message with file ID and link
    """
    try:
        result = await drive_service.create_file(
            name=params.name,
            content=params.content,
            mime_type=params.mime_type,
            folder_id=params.folder_id
        )

        return create_success_response(
            f"Created file '{result.get('name')}'",
            data={
                "file_id": result.get('id'),
                "web_link": result.get('webViewLink', 'N/A'),
                "mime_type": result.get('mimeType')
            },
            response_format=params.response_format
        )

    except Exception as e:
        logger.error(f"drive_create_file error: {str(e)}")
        return format_error(e, "creating file")


@mcp.tool(
    name="drive_update_file",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def drive_update_file(params: DriveUpdateFileInput) -> str:
    """Update an existing file in Google Drive.

    Updates file content and/or renames a file. At least one of content or name
    must be provided.

    Args:
        params (DriveUpdateFileInput): Update parameters

    Returns:
        str: Success message with updated file info
    """
    try:
        if not params.content and not params.name:
            return format_error(
                ValueError("Either 'content' or 'name' must be provided"),
                "validating input"
            )

        result = await drive_service.update_file(
            file_id=params.file_id,
            content=params.content,
            name=params.name
        )

        return create_success_response(
            f"Updated file '{result.get('name')}'",
            data={
                "file_id": result.get('id'),
                "modified_time": result.get('modifiedTime')
            },
            response_format=params.response_format
        )

    except Exception as e:
        logger.error(f"drive_update_file error: {str(e)}")
        return format_error(e, "updating file")


@mcp.tool(
    name="drive_delete_file",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def drive_delete_file(params: DriveDeleteFileInput) -> str:
    """Delete a file from Google Drive.

    ⚠️ WARNING: This operation is destructive and moves the file to trash.
    The file can be restored from trash within 30 days.

    Args:
        params (DriveDeleteFileInput): File ID to delete

    Returns:
        str: Success confirmation message
    """
    try:
        await drive_service.delete_file(params.file_id)
        return create_success_response(
            f"Deleted file with ID: {params.file_id}",
            data={"note": "File moved to trash, can be restored within 30 days"}
        )

    except Exception as e:
        logger.error(f"drive_delete_file error: {str(e)}")
        return format_error(e, "deleting file")


@mcp.tool(
    name="drive_upload_file",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def drive_upload_file(params: DriveUploadFileInput) -> str:
    """Upload a local file to Google Drive.

    Uploads a file from the local filesystem to Google Drive. The MIME type
    is automatically detected from the file extension.

    Args:
        params (DriveUploadFileInput): Upload parameters

    Returns:
        str: Success message with uploaded file info
    """
    try:
        result = await drive_service.upload_file(
            local_path=params.local_path,
            name=params.name,
            folder_id=params.folder_id
        )

        return create_success_response(
            f"Uploaded file '{result.get('name')}'",
            data={
                "file_id": result.get('id'),
                "web_link": result.get('webViewLink', 'N/A'),
                "size": result.get('size', 'unknown')
            },
            response_format=params.response_format
        )

    except Exception as e:
        logger.error(f"drive_upload_file error: {str(e)}")
        return format_error(e, "uploading file")


@mcp.tool(
    name="drive_download_file",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def drive_download_file(params: DriveDownloadFileInput) -> str:
    """Download a file from Google Drive to local system.

    Downloads a file and saves it to the specified local path. For Google Docs,
    Sheets, and Slides, you can specify an export MIME type.

    Args:
        params (DriveDownloadFileInput): Download parameters

    Returns:
        str: Success message with download info
    """
    try:
        result = await drive_service.download_file(
            file_id=params.file_id,
            local_path=params.local_path,
            mime_type=params.mime_type
        )

        return create_success_response(
            f"Downloaded file to: {params.local_path}",
            data={
                "file_size_bytes": result.get('size', 'unknown')
            }
        )

    except Exception as e:
        logger.error(f"drive_download_file error: {str(e)}")
        return format_error(e, "downloading file")


@mcp.tool(
    name="drive_list_shared_drives",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def drive_list_shared_drives(params: DriveListSharedDrivesInput) -> str:
    """List all shared drives (Team Drives) accessible to the user.

    Retrieves all shared drives (formerly Team Drives) that the authenticated
    user has access to. Includes drive names and IDs.

    Args:
        params (DriveListSharedDrivesInput): List parameters with pagination

    Returns:
        str: List of shared drives with metadata
    """
    try:
        result = await drive_service.list_shared_drives(max_results=params.limit)

        if not result:
            return "No shared drives found."

        # Apply pagination
        total_count = len(result)
        paginated_result = result[params.offset:params.offset + params.limit]
        has_more = (params.offset + params.limit) < total_count

        if params.response_format == ResponseFormat.JSON:
            pagination = format_pagination_metadata(
                total=total_count,
                count=len(paginated_result),
                offset=params.offset,
                has_more=has_more,
                next_offset=params.offset + params.limit if has_more else None
            )
            return json.dumps({
                "shared_drives": paginated_result,
                "pagination": pagination
            }, indent=2)

        # Markdown format
        response = f"# Shared Drives ({total_count} found)\n\n"
        for drive in paginated_result:
            response += f"## {drive.get('name', 'Unnamed')}\n"
            response += f"- **ID**: `{drive.get('id')}`\n\n"

        if has_more:
            response += f"\n📄 Use offset={params.offset + params.limit} to see more results."

        return response

    except Exception as e:
        logger.error(f"drive_list_shared_drives error: {str(e)}")
        return format_error(e, "listing shared drives")
