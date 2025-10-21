"""MCP tools for Google Docs operations."""

from typing import Any, Dict, List
from mcp.types import Tool, TextContent

from ..services.docs_service import DocsService
from ..utils.logger import setup_logger
from ..utils.error_handler import GoogleWorkspaceError

logger = setup_logger(__name__)

# Initialize Docs service
docs_service = DocsService()


# Tool definitions
DOCS_TOOLS = [
    Tool(
        name="docs_create",
        description="Create a new Google Docs document",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Document title"
                }
            },
            "required": ["title"]
        }
    ),
    Tool(
        name="docs_read",
        description="Read content from a Google Docs document",
        inputSchema={
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "description": "Google Docs document ID"
                }
            },
            "required": ["document_id"]
        }
    ),
    Tool(
        name="docs_update",
        description="Update content in a Google Docs document",
        inputSchema={
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "description": "Google Docs document ID"
                },
                "text": {
                    "type": "string",
                    "description": "Text content to insert"
                },
                "index": {
                    "type": "integer",
                    "description": "Position to insert text (default: 1)",
                    "default": 1
                }
            },
            "required": ["document_id", "text"]
        }
    ),
    Tool(
        name="docs_delete",
        description="Delete a Google Docs document",
        inputSchema={
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "description": "Google Docs document ID to delete"
                }
            },
            "required": ["document_id"]
        }
    )
]


async def handle_docs_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle Docs tool execution.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        List of TextContent responses
    """
    try:
        if name == "docs_create":
            result = await docs_service.create_document(**arguments)
            return [TextContent(
                type="text",
                text=f"Created document: {result['title']}\n"
                     f"Document ID: {result['documentId']}\n"
                     f"URL: https://docs.google.com/document/d/{result['documentId']}"
            )]

        elif name == "docs_read":
            result = await docs_service.read_document(**arguments)
            return [TextContent(
                type="text",
                text=f"Document: {result['title']}\n"
                     f"Document ID: {result['document_id']}\n\n"
                     f"Content:\n{result['content']}"
            )]

        elif name == "docs_update":
            result = await docs_service.update_document(**arguments)
            return [TextContent(
                type="text",
                text=f"Successfully updated document: {arguments['document_id']}\n"
                     f"Inserted text at index {arguments.get('index', 1)}"
            )]

        elif name == "docs_delete":
            await docs_service.delete_document(arguments['document_id'])
            return [TextContent(
                type="text",
                text=f"Successfully deleted document: {arguments['document_id']}"
            )]

        else:
            raise GoogleWorkspaceError(f"Unknown Docs tool: {name}")

    except GoogleWorkspaceError as e:
        logger.error(f"Docs tool error: {e.message}")
        return [TextContent(
            type="text",
            text=f"Error: {e.message}\nDetails: {e.details}"
        )]
