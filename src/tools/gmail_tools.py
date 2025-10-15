"""MCP tools for Gmail operations."""

from typing import Any, Dict, List
from mcp.types import Tool, TextContent

from ..services.gmail_service import GmailService
from ..utils.logger import setup_logger
from ..utils.error_handler import GoogleWorkspaceError

logger = setup_logger(__name__)

# Initialize Gmail service
gmail_service = GmailService()


# Tool definitions
GMAIL_TOOLS = [
    Tool(
        name="gmail_search_messages",
        description="Search for messages in Gmail using query syntax",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Gmail search query (e.g., 'from:user@example.com subject:report')",
                    "default": ""
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 100)",
                    "default": 100
                },
                "label_ids": {
                    "type": "array",
                    "description": "Filter by label IDs (e.g., ['INBOX', 'UNREAD'])",
                    "items": {
                        "type": "string"
                    }
                }
            }
        }
    ),
    Tool(
        name="gmail_read_message",
        description="Read full content of a Gmail message",
        inputSchema={
            "type": "object",
            "properties": {
                "message_id": {
                    "type": "string",
                    "description": "Gmail message ID"
                }
            },
            "required": ["message_id"]
        }
    ),
    Tool(
        name="gmail_send_message",
        description="Send a new email message",
        inputSchema={
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email address"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject"
                },
                "body": {
                    "type": "string",
                    "description": "Email body content"
                },
                "cc": {
                    "type": "string",
                    "description": "CC email address (optional)"
                },
                "bcc": {
                    "type": "string",
                    "description": "BCC email address (optional)"
                }
            },
            "required": ["to", "subject", "body"]
        }
    ),
    Tool(
        name="gmail_reply_message",
        description="Reply to an existing email message",
        inputSchema={
            "type": "object",
            "properties": {
                "message_id": {
                    "type": "string",
                    "description": "Gmail message ID to reply to"
                },
                "body": {
                    "type": "string",
                    "description": "Reply body content"
                }
            },
            "required": ["message_id", "body"]
        }
    ),
    Tool(
        name="gmail_delete_message",
        description="Delete (move to trash) a Gmail message",
        inputSchema={
            "type": "object",
            "properties": {
                "message_id": {
                    "type": "string",
                    "description": "Gmail message ID to delete"
                }
            },
            "required": ["message_id"]
        }
    ),
    Tool(
        name="gmail_list_labels",
        description="List all Gmail labels",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    Tool(
        name="gmail_modify_labels",
        description="Add or remove labels from a message",
        inputSchema={
            "type": "object",
            "properties": {
                "message_id": {
                    "type": "string",
                    "description": "Gmail message ID"
                },
                "add_labels": {
                    "type": "array",
                    "description": "Label IDs to add",
                    "items": {
                        "type": "string"
                    }
                },
                "remove_labels": {
                    "type": "array",
                    "description": "Label IDs to remove",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": ["message_id"]
        }
    )
]


async def handle_gmail_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle Gmail tool execution.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        List of TextContent responses
    """
    try:
        if name == "gmail_search_messages":
            results = await gmail_service.search_messages(**arguments)

            if not results:
                return [TextContent(
                    type="text",
                    text="No messages found matching the query."
                )]

            messages_text = []
            for msg in results[:20]:  # Limit display to 20
                headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}
                messages_text.append(
                    f"ID: {msg['id']}\n"
                    f"  From: {headers.get('From', 'N/A')}\n"
                    f"  Subject: {headers.get('Subject', 'N/A')}\n"
                    f"  Date: {headers.get('Date', 'N/A')}\n"
                    f"  Snippet: {msg.get('snippet', 'N/A')[:100]}..."
                )

            return [TextContent(
                type="text",
                text=f"Found {len(results)} messages (showing first 20):\n\n" +
                     "\n\n".join(messages_text)
            )]

        elif name == "gmail_read_message":
            result = await gmail_service.read_message(**arguments)
            return [TextContent(
                type="text",
                text=f"Message ID: {result['message_id']}\n"
                     f"Thread ID: {result['thread_id']}\n"
                     f"From: {result['headers'].get('From', 'N/A')}\n"
                     f"To: {result['headers'].get('To', 'N/A')}\n"
                     f"Subject: {result['headers'].get('Subject', 'N/A')}\n"
                     f"Date: {result['headers'].get('Date', 'N/A')}\n"
                     f"Labels: {', '.join(result['labels'])}\n\n"
                     f"Body:\n{result['body']}"
            )]

        elif name == "gmail_send_message":
            result = await gmail_service.send_message(**arguments)
            return [TextContent(
                type="text",
                text=f"Successfully sent message!\n"
                     f"Message ID: {result['id']}\n"
                     f"To: {arguments['to']}\n"
                     f"Subject: {arguments['subject']}"
            )]

        elif name == "gmail_reply_message":
            result = await gmail_service.reply_message(**arguments)
            return [TextContent(
                type="text",
                text=f"Successfully replied to message!\n"
                     f"Original Message ID: {arguments['message_id']}\n"
                     f"Reply Message ID: {result['id']}"
            )]

        elif name == "gmail_delete_message":
            await gmail_service.delete_message(arguments['message_id'])
            return [TextContent(
                type="text",
                text=f"Successfully moved message to trash: {arguments['message_id']}"
            )]

        elif name == "gmail_list_labels":
            labels = await gmail_service.list_labels()
            labels_text = "\n".join([
                f"- {label['name']} (ID: {label['id']})"
                for label in labels
            ])
            return [TextContent(
                type="text",
                text=f"Found {len(labels)} labels:\n\n{labels_text}"
            )]

        elif name == "gmail_modify_labels":
            result = await gmail_service.modify_labels(**arguments)
            added = arguments.get('add_labels', [])
            removed = arguments.get('remove_labels', [])

            changes = []
            if added:
                changes.append(f"Added labels: {', '.join(added)}")
            if removed:
                changes.append(f"Removed labels: {', '.join(removed)}")

            return [TextContent(
                type="text",
                text=f"Successfully modified labels for message: {arguments['message_id']}\n" +
                     "\n".join(changes)
            )]

        else:
            raise GoogleWorkspaceError(f"Unknown Gmail tool: {name}")

    except GoogleWorkspaceError as e:
        logger.error(f"Gmail tool error: {e.message}")
        return [TextContent(
            type="text",
            text=f"Error: {e.message}\nDetails: {e.details}"
        )]
