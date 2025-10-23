"""Response formatting utilities for Google Workspace MCP tools."""

import json
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


# Character limit for responses (MCP best practice)
CHARACTER_LIMIT = 25000


class ResponseFormat(str, Enum):
    """Output format options for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


def format_timestamp(timestamp: Optional[str]) -> str:
    """Convert ISO timestamp to human-readable format.

    Args:
        timestamp: ISO format timestamp string

    Returns:
        Human-readable timestamp or 'N/A' if None
    """
    if not timestamp:
        return "N/A"

    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return timestamp


def format_file_list(files: List[Dict[str, Any]], response_format: ResponseFormat) -> str:
    """Format a list of files for output.

    Args:
        files: List of file metadata dictionaries
        response_format: Output format (markdown or json)

    Returns:
        Formatted file list string
    """
    if not files:
        return "No files found."

    if response_format == ResponseFormat.JSON:
        return json.dumps({"files": files, "count": len(files)}, indent=2)

    # Markdown format
    lines = [f"# Files ({len(files)} found)\n"]
    for file in files:
        name = file.get('name', 'Unnamed')
        file_id = file.get('id', 'N/A')
        mime_type = file.get('mimeType', 'unknown')
        modified = format_timestamp(file.get('modifiedTime'))
        web_link = file.get('webViewLink', '')

        lines.append(f"## {name}")
        lines.append(f"- **ID**: `{file_id}`")
        lines.append(f"- **Type**: {mime_type}")
        lines.append(f"- **Modified**: {modified}")
        if web_link:
            lines.append(f"- **Link**: {web_link}")
        lines.append("")

    return "\n".join(lines)


def format_pagination_metadata(
    total: Optional[int],
    count: int,
    offset: int,
    has_more: bool,
    next_offset: Optional[int] = None
) -> Dict[str, Any]:
    """Create pagination metadata dictionary.

    Args:
        total: Total number of items available
        count: Number of items in current response
        offset: Current offset position
        has_more: Whether more items are available
        next_offset: Offset for next page if has_more is True

    Returns:
        Pagination metadata dictionary
    """
    metadata = {
        "count": count,
        "offset": offset,
        "has_more": has_more
    }

    if total is not None:
        metadata["total"] = total

    if has_more and next_offset is not None:
        metadata["next_offset"] = next_offset

    return metadata


def truncate_response(
    response_text: str,
    items: Optional[List[Any]] = None,
    item_formatter: Optional[callable] = None
) -> str:
    """Truncate response if it exceeds CHARACTER_LIMIT.

    Args:
        response_text: Full response text
        items: Optional list of items to truncate intelligently
        item_formatter: Optional function to format individual items

    Returns:
        Potentially truncated response with truncation notice
    """
    if len(response_text) <= CHARACTER_LIMIT:
        return response_text

    # If items are provided, try to truncate by removing items
    if items and item_formatter:
        truncated_items = []
        current_length = 0
        reserve_space = 500  # Reserve space for truncation message

        for item in items:
            formatted_item = item_formatter(item)
            if current_length + len(formatted_item) + reserve_space > CHARACTER_LIMIT:
                break
            truncated_items.append(item)
            current_length += len(formatted_item)

        truncated_text = item_formatter(truncated_items) if truncated_items else ""
        truncation_message = (
            f"\n\n⚠️ **Response Truncated**\n"
            f"Showing {len(truncated_items)} of {len(items)} items. "
            f"Use 'limit' and 'offset' parameters or add filters to see more results."
        )

        return truncated_text + truncation_message

    # Simple truncation
    truncated = response_text[:CHARACTER_LIMIT - 500]
    truncation_message = (
        f"\n\n⚠️ **Response Truncated**\n"
        f"Response exceeded {CHARACTER_LIMIT} character limit. "
        f"Use pagination parameters or filters to reduce result size."
    )

    return truncated + truncation_message


def format_error(error: Exception, context: str = "") -> str:
    """Format error message for tool responses.

    Args:
        error: Exception object
        context: Optional context about what operation failed

    Returns:
        Formatted error message
    """
    error_msg = f"❌ **Error**: {str(error)}"

    if context:
        error_msg = f"❌ **Error** ({context}): {str(error)}"

    # Add suggestions based on error type
    error_str = str(error).lower()
    if "not found" in error_str or "404" in error_str:
        error_msg += "\n\n💡 **Suggestion**: Verify the ID and ensure you have access to this resource."
    elif "permission" in error_str or "403" in error_str:
        error_msg += "\n\n💡 **Suggestion**: Check that you have the necessary permissions for this operation."
    elif "quota" in error_str or "rate limit" in error_str:
        error_msg += "\n\n💡 **Suggestion**: You've hit API rate limits. Wait a moment and try again."
    elif "authentication" in error_str or "401" in error_str:
        error_msg += "\n\n💡 **Suggestion**: Your authentication token may have expired. Re-authenticate using the server."

    return error_msg


def create_success_response(
    message: str,
    data: Optional[Dict[str, Any]] = None,
    response_format: ResponseFormat = ResponseFormat.MARKDOWN
) -> str:
    """Create a standardized success response.

    Args:
        message: Success message
        data: Optional data to include
        response_format: Output format

    Returns:
        Formatted success response
    """
    if response_format == ResponseFormat.JSON:
        response = {"success": True, "message": message}
        if data:
            response["data"] = data
        return json.dumps(response, indent=2)

    # Markdown format
    result = f"✅ **Success**: {message}"

    if data:
        result += "\n\n**Details:**"
        for key, value in data.items():
            result += f"\n- **{key.replace('_', ' ').title()}**: {value}"

    return result
