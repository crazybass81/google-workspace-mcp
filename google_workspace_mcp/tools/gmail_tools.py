"""MCP tools for Gmail operations using FastMCP."""

import json
from typing import Optional, List
from pydantic import Field, field_validator, EmailStr

from ..server_fastmcp import mcp
from ..services.gmail_service import GmailService
from ..utils.logger import setup_logger
from ..utils.base_models import BaseMCPInput, MessageIdInput, BaseListInput
from ..utils.response_formatter import (
    ResponseFormat,
    format_error,
    create_success_response,
    CHARACTER_LIMIT
)

logger = setup_logger(__name__)
gmail_service = GmailService()


# ============================================================================
# Pydantic Input Models
# ============================================================================

class GmailSearchInput(BaseListInput):
    """Input model for searching Gmail messages."""

    query: str = Field(
        default="",
        description="Gmail search query using Gmail syntax (e.g., 'from:user@example.com subject:report is:unread', 'after:2025/10/01')",
        max_length=500
    )
    label_ids: Optional[List[str]] = Field(
        default=None,
        description="Filter by label IDs (e.g., ['INBOX', 'UNREAD', 'IMPORTANT'])"
    )


class GmailReadInput(MessageIdInput):
    """Input model for reading a Gmail message."""

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class GmailSendInput(BaseMCPInput):
    """Input model for sending a new Gmail message."""

    to: str = Field(
        ...,
        description="Recipient email address (e.g., 'user@example.com')",
        min_length=3,
        max_length=320  # RFC 5321 email length limit
    )
    subject: str = Field(
        ...,
        description="Email subject line",
        max_length=500
    )
    body: str = Field(
        ...,
        description="Email body content (plain text or HTML)",
        max_length=1000000  # 1MB limit
    )
    cc: Optional[str] = Field(
        default=None,
        description="CC email address (optional)",
        max_length=320
    )
    bcc: Optional[str] = Field(
        default=None,
        description="BCC email address (optional)",
        max_length=320
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )

    @field_validator('to', 'cc', 'bcc')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Basic email format validation."""
        if v and '@' not in v:
            raise ValueError("Invalid email format - must contain '@'")
        return v


class GmailReplyInput(MessageIdInput):
    """Input model for replying to a Gmail message."""

    body: str = Field(
        ...,
        description="Reply body content",
        max_length=1000000
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class GmailListLabelsInput(BaseMCPInput):
    """Input model for listing Gmail labels."""

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class GmailModifyLabelsInput(MessageIdInput):
    """Input model for modifying message labels."""

    add_labels: Optional[List[str]] = Field(
        default=None,
        description="Label IDs to add (e.g., ['STARRED', 'IMPORTANT'])"
    )
    remove_labels: Optional[List[str]] = Field(
        default=None,
        description="Label IDs to remove (e.g., ['UNREAD', 'SPAM'])"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )

    @field_validator('add_labels', 'remove_labels')
    @classmethod
    def validate_labels_not_empty(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Ensure at least one label operation is specified."""
        return v


# ============================================================================
# Tool Implementations
# ============================================================================

@mcp.tool(
    name="gmail_search_messages",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def gmail_search_messages(params: GmailSearchInput) -> str:
    """Search for messages in Gmail using Gmail search syntax.

    Searches Gmail messages using the same query syntax as the Gmail web interface.
    Returns message metadata including sender, subject, snippet, and labels.

    Use this when you need to:
    - Find specific emails by sender, subject, or content
    - Filter messages by labels or date ranges
    - Search across all Gmail folders

    Args:
        params (GmailSearchInput): Validated parameters with:
            - query: Gmail search query (e.g., 'from:user@example.com')
            - label_ids: Optional filter by label IDs
            - limit: Maximum results (default 20)
            - response_format: Output format (markdown/json)

    Returns:
        str: List of matching messages with metadata

    Examples:
        - Search by sender: query='from:boss@company.com'
        - Search unread: query='is:unread'
        - Search by date: query='after:2025/10/01 before:2025/10/31'
        - Complex search: query='from:user@example.com subject:report is:unread'
        - Filter by labels: label_ids=['INBOX', 'IMPORTANT']

    Gmail Search Syntax:
        - from:sender@example.com - From specific sender
        - to:recipient@example.com - To specific recipient
        - subject:keyword - Subject contains keyword
        - is:unread - Unread messages
        - is:starred - Starred messages
        - has:attachment - Messages with attachments
        - after:2025/10/01 - After specific date
        - before:2025/10/31 - Before specific date
    """
    try:
        # Call Gmail service
        kwargs = {
            "query": params.query,
            "max_results": params.limit
        }
        if params.label_ids:
            kwargs["label_ids"] = params.label_ids

        results = await gmail_service.search_messages(**kwargs)

        if not results:
            return "No messages found matching the search criteria."

        # Apply pagination
        total_count = len(results)
        paginated_results = results[params.offset:params.offset + params.limit]
        has_more = (params.offset + params.limit) < total_count

        if params.response_format == ResponseFormat.JSON:
            response = {
                "messages": paginated_results[:20],  # Limit for readability
                "total_count": total_count,
                "showing": len(paginated_results)
            }
            return json.dumps(response, indent=2)

        # Markdown format
        response = f"# Gmail Search Results\n\n"
        response += f"**Query**: `{params.query or 'all messages'}`\n"
        response += f"**Found**: {total_count} messages\n"
        response += f"**Showing**: {len(paginated_results)}\n\n"

        # Show first 20 messages
        for idx, msg in enumerate(paginated_results[:20], 1):
            headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}
            response += f"## {idx}. {headers.get('Subject', '(No subject)')}\n"
            response += f"- **From**: {headers.get('From', 'Unknown')}\n"
            response += f"- **Date**: {headers.get('Date', 'Unknown')}\n"
            response += f"- **ID**: `{msg['id']}`\n"
            response += f"- **Snippet**: {msg.get('snippet', 'N/A')[:100]}...\n\n"

        if total_count > 20:
            response += f"\n💡 **Tip**: Showing first 20 of {total_count} results. Use more specific search query to narrow results.\n"

        if has_more:
            response += f"\n📄 **Pagination**: Use offset={params.offset + params.limit} for more results.\n"

        return response

    except Exception as e:
        logger.error(f"gmail_search_messages error: {str(e)}")
        return format_error(e, "searching messages")


@mcp.tool(
    name="gmail_read_message",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def gmail_read_message(params: GmailReadInput) -> str:
    """Read full content of a Gmail message.

    Retrieves the complete content of a specific Gmail message including headers,
    body, and metadata. Use gmail_search_messages first to find message IDs.

    Use this when you need to:
    - Read complete email content
    - Extract email headers and metadata
    - Access full message body

    Args:
        params (GmailReadInput): Validated parameters with:
            - message_id: Gmail message ID
            - response_format: Output format (markdown/json)

    Returns:
        str: Complete message content with headers and body

    Examples:
        - Read message: message_id='18a1b2c3d4e5f6g7'

    Note:
        - Message IDs can be obtained from gmail_search_messages
        - Body may be truncated if exceeding 25,000 characters
        - HTML emails are converted to plain text
    """
    try:
        result = await gmail_service.read_message(message_id=params.message_id)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2)

        # Markdown format
        headers = result.get('headers', {})
        response = f"# Email: {headers.get('Subject', '(No subject)')}\n\n"
        response += f"**Message ID**: `{result['message_id']}`\n"
        response += f"**Thread ID**: `{result['thread_id']}`\n"
        response += f"**From**: {headers.get('From', 'Unknown')}\n"
        response += f"**To**: {headers.get('To', 'Unknown')}\n"
        if headers.get('Cc'):
            response += f"**Cc**: {headers['Cc']}\n"
        response += f"**Date**: {headers.get('Date', 'Unknown')}\n"
        response += f"**Labels**: {', '.join(result.get('labels', []))}\n\n"

        response += f"## Body\n\n{result.get('body', 'No content')}"

        # Check character limit
        if len(response) > CHARACTER_LIMIT:
            truncated = response[:CHARACTER_LIMIT - 200]
            truncated += "\n\n⚠️ **Content Truncated**: Email content exceeds character limit (25,000 chars)."
            return truncated

        return response

    except Exception as e:
        logger.error(f"gmail_read_message error: {str(e)}")
        return format_error(e, "reading message")


@mcp.tool(
    name="gmail_send_message",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def gmail_send_message(params: GmailSendInput) -> str:
    """Send a new email message via Gmail.

    Sends a new email message from the authenticated user's Gmail account.
    Supports CC and BCC recipients.

    Use this when you need to:
    - Send automated email notifications
    - Reply programmatically to contacts
    - Send reports or updates

    Args:
        params (GmailSendInput): Validated parameters with:
            - to: Recipient email address
            - subject: Email subject
            - body: Email body content
            - cc: Optional CC address
            - bcc: Optional BCC address
            - response_format: Output format (markdown/json)

    Returns:
        str: Confirmation with sent message ID

    Examples:
        - Simple email: to='user@example.com', subject='Hello', body='Message content'
        - With CC: to='user@example.com', cc='manager@example.com', subject='Report'
        - With BCC: to='user@example.com', bcc='archive@example.com'

    Note:
        - Message is sent immediately
        - Cannot be unsent after sending
        - Gmail may apply sending limits
    """
    try:
        result = await gmail_service.send_message(
            to=params.to,
            subject=params.subject,
            body=params.body,
            cc=params.cc,
            bcc=params.bcc
        )

        return create_success_response(
            f"Sent email to {params.to}",
            data={
                "message_id": result.get('id'),
                "to": params.to,
                "subject": params.subject,
                "cc": params.cc,
                "bcc": params.bcc
            },
            response_format=params.response_format
        )

    except Exception as e:
        logger.error(f"gmail_send_message error: {str(e)}")
        return format_error(e, "sending message")


@mcp.tool(
    name="gmail_reply_message",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def gmail_reply_message(params: GmailReplyInput) -> str:
    """Reply to an existing Gmail message.

    Sends a reply to a specific message, maintaining the email thread.
    The reply is sent to the original sender and includes the original thread.

    Use this when you need to:
    - Reply to received emails
    - Maintain email conversation threads
    - Respond programmatically

    Args:
        params (GmailReplyInput): Validated parameters with:
            - message_id: Original message ID to reply to
            - body: Reply content
            - response_format: Output format (markdown/json)

    Returns:
        str: Confirmation with reply message ID

    Examples:
        - Reply to message: message_id='18a1b2c3d4e5f6g7', body='Thank you for your email...'

    Note:
        - Reply maintains the original thread
        - Reply is sent to the original sender
        - Subject is automatically prefixed with "Re:"
    """
    try:
        result = await gmail_service.reply_message(
            message_id=params.message_id,
            body=params.body
        )

        return create_success_response(
            f"Sent reply to message {params.message_id}",
            data={
                "original_message_id": params.message_id,
                "reply_message_id": result.get('id')
            },
            response_format=params.response_format
        )

    except Exception as e:
        logger.error(f"gmail_reply_message error: {str(e)}")
        return format_error(e, "replying to message")


@mcp.tool(
    name="gmail_list_labels",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def gmail_list_labels(params: GmailListLabelsInput) -> str:
    """List all Gmail labels for the authenticated user.

    Retrieves all labels including system labels (INBOX, SENT, TRASH) and
    user-created custom labels.

    Use this when you need to:
    - Discover available labels
    - Find label IDs for filtering
    - Manage label organization

    Args:
        params (GmailListLabelsInput): Validated parameters with:
            - response_format: Output format (markdown/json)

    Returns:
        str: List of all labels with IDs and names

    Examples:
        - List all labels: (no parameters required)

    Note:
        - Includes both system and user-created labels
        - Label IDs can be used in search and modify operations
        - System labels: INBOX, SENT, TRASH, SPAM, STARRED, etc.
    """
    try:
        labels = await gmail_service.list_labels()

        if params.response_format == ResponseFormat.JSON:
            return json.dumps({"labels": labels}, indent=2)

        # Markdown format
        response = f"# Gmail Labels ({len(labels)} total)\n\n"

        # Separate system and user labels
        system_labels = [l for l in labels if l['id'].isupper() or l['id'].startswith('Label_')]
        user_labels = [l for l in labels if l not in system_labels]

        if system_labels:
            response += "## System Labels\n\n"
            for label in system_labels:
                response += f"- **{label['name']}** (ID: `{label['id']}`)\n"

        if user_labels:
            response += "\n## User Labels\n\n"
            for label in user_labels:
                response += f"- **{label['name']}** (ID: `{label['id']}`)\n"

        return response

    except Exception as e:
        logger.error(f"gmail_list_labels error: {str(e)}")
        return format_error(e, "listing labels")


@mcp.tool(
    name="gmail_modify_labels",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def gmail_modify_labels(params: GmailModifyLabelsInput) -> str:
    """Add or remove labels from a Gmail message.

    Modifies the labels on a specific message by adding and/or removing labels.
    At least one of add_labels or remove_labels must be specified.

    Use this when you need to:
    - Organize messages with labels
    - Mark messages as read/unread
    - Star or unstar messages
    - Move messages between folders

    Args:
        params (GmailModifyLabelsInput): Validated parameters with:
            - message_id: Message ID to modify
            - add_labels: Optional list of label IDs to add
            - remove_labels: Optional list of label IDs to remove
            - response_format: Output format (markdown/json)

    Returns:
        str: Confirmation of label modifications

    Examples:
        - Mark as read: message_id='18a1...', remove_labels=['UNREAD']
        - Star message: message_id='18a1...', add_labels=['STARRED']
        - Archive: message_id='18a1...', remove_labels=['INBOX']
        - Multiple: add_labels=['IMPORTANT'], remove_labels=['UNREAD']

    Common Label IDs:
        - INBOX, SENT, TRASH, SPAM, DRAFT
        - STARRED, IMPORTANT, UNREAD
        - Custom label IDs from gmail_list_labels

    Note:
        - Label changes are immediate
        - Use gmail_list_labels to find label IDs
        - Cannot add and remove the same label simultaneously
    """
    try:
        if not params.add_labels and not params.remove_labels:
            return format_error(
                ValueError("Must specify at least one of add_labels or remove_labels"),
                "validating input"
            )

        result = await gmail_service.modify_labels(
            message_id=params.message_id,
            add_labels=params.add_labels,
            remove_labels=params.remove_labels
        )

        changes = []
        if params.add_labels:
            changes.append(f"Added: {', '.join(params.add_labels)}")
        if params.remove_labels:
            changes.append(f"Removed: {', '.join(params.remove_labels)}")

        return create_success_response(
            f"Modified labels for message {params.message_id}",
            data={
                "message_id": params.message_id,
                "changes": " | ".join(changes)
            },
            response_format=params.response_format
        )

    except Exception as e:
        logger.error(f"gmail_modify_labels error: {str(e)}")
        return format_error(e, "modifying labels")
