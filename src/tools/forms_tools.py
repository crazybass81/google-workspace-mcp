"""MCP tools for Google Forms operations."""

from typing import Any, Dict, List
from mcp.types import Tool, TextContent

from ..services.forms_service import FormsService
from ..utils.logger import setup_logger
from ..utils.error_handler import GoogleWorkspaceError

logger = setup_logger(__name__)

# Initialize Forms service
forms_service = FormsService()


# Tool definitions
FORMS_TOOLS = [
    Tool(
        name="forms_create",
        description="Create a new Google Form",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Form title"
                },
                "document_title": {
                    "type": "string",
                    "description": "Document title (optional, defaults to title)"
                }
            },
            "required": ["title"]
        }
    ),
    Tool(
        name="forms_read",
        description="Read structure of a Google Form",
        inputSchema={
            "type": "object",
            "properties": {
                "form_id": {
                    "type": "string",
                    "description": "Google Forms form ID"
                }
            },
            "required": ["form_id"]
        }
    ),
    Tool(
        name="forms_update",
        description="Update form structure and questions",
        inputSchema={
            "type": "object",
            "properties": {
                "form_id": {
                    "type": "string",
                    "description": "Google Forms form ID"
                },
                "requests": {
                    "type": "array",
                    "description": "Array of update requests",
                    "items": {
                        "type": "object"
                    }
                }
            },
            "required": ["form_id", "requests"]
        }
    ),
    Tool(
        name="forms_delete",
        description="Delete a Google Form",
        inputSchema={
            "type": "object",
            "properties": {
                "form_id": {
                    "type": "string",
                    "description": "Google Forms form ID to delete"
                }
            },
            "required": ["form_id"]
        }
    ),
    Tool(
        name="forms_get_responses",
        description="Get responses submitted to a Google Form",
        inputSchema={
            "type": "object",
            "properties": {
                "form_id": {
                    "type": "string",
                    "description": "Google Forms form ID"
                }
            },
            "required": ["form_id"]
        }
    )
]


async def handle_forms_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle Forms tool execution.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        List of TextContent responses
    """
    try:
        if name == "forms_create":
            result = await forms_service.create_form(**arguments)
            return [TextContent(
                type="text",
                text=f"Created form: {result['info']['title']}\n"
                     f"Form ID: {result['formId']}\n"
                     f"URL: https://docs.google.com/forms/d/{result['formId']}/edit"
            )]

        elif name == "forms_read":
            result = await forms_service.read_form(**arguments)
            items_info = "\n".join([
                f"  Item {i+1}: {item['title']} (Type: {item['question_type']})"
                for i, item in enumerate(result['items'])
            ])
            return [TextContent(
                type="text",
                text=f"Form: {result['title']}\n"
                     f"Form ID: {result['form_id']}\n"
                     f"Total items: {result['item_count']}\n\n"
                     f"Items:\n{items_info}"
            )]

        elif name == "forms_update":
            result = await forms_service.update_form(**arguments)
            return [TextContent(
                type="text",
                text=f"Successfully updated form: {arguments['form_id']}\n"
                     f"Form URL: https://docs.google.com/forms/d/{arguments['form_id']}/edit"
            )]

        elif name == "forms_delete":
            await forms_service.delete_form(arguments['form_id'])
            return [TextContent(
                type="text",
                text=f"Successfully deleted form: {arguments['form_id']}"
            )]

        elif name == "forms_get_responses":
            result = await forms_service.get_responses(**arguments)
            return [TextContent(
                type="text",
                text=f"Form ID: {result['form_id']}\n"
                     f"Total responses: {result['response_count']}\n\n"
                     f"Recent responses retrieved. Use the response data for detailed analysis."
            )]

        else:
            raise GoogleWorkspaceError(f"Unknown Forms tool: {name}")

    except GoogleWorkspaceError as e:
        logger.error(f"Forms tool error: {e.message}")
        return [TextContent(
            type="text",
            text=f"Error: {e.message}\nDetails: {e.details}"
        )]
