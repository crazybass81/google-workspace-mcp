"""MCP tools for Google Slides operations."""

from typing import Any, Dict, List
from mcp.types import Tool, TextContent

from ..services.slides_service import SlidesService
from ..utils.logger import setup_logger
from ..utils.error_handler import GoogleWorkspaceError

logger = setup_logger(__name__)

# Initialize Slides service
slides_service = SlidesService()


# Tool definitions
SLIDES_TOOLS = [
    Tool(
        name="slides_create",
        description="Create a new Google Slides presentation",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Presentation title"
                }
            },
            "required": ["title"]
        }
    ),
    Tool(
        name="slides_read",
        description="Read structure of a Google Slides presentation",
        inputSchema={
            "type": "object",
            "properties": {
                "presentation_id": {
                    "type": "string",
                    "description": "Google Slides presentation ID"
                }
            },
            "required": ["presentation_id"]
        }
    ),
    Tool(
        name="slides_add_slide",
        description="Add a new slide to a presentation",
        inputSchema={
            "type": "object",
            "properties": {
                "presentation_id": {
                    "type": "string",
                    "description": "Google Slides presentation ID"
                },
                "insertion_index": {
                    "type": "integer",
                    "description": "Position to insert slide (optional)"
                }
            },
            "required": ["presentation_id"]
        }
    ),
    Tool(
        name="slides_update",
        description="Update slide content with batch requests",
        inputSchema={
            "type": "object",
            "properties": {
                "presentation_id": {
                    "type": "string",
                    "description": "Google Slides presentation ID"
                },
                "requests": {
                    "type": "array",
                    "description": "Array of update requests",
                    "items": {
                        "type": "object"
                    }
                }
            },
            "required": ["presentation_id", "requests"]
        }
    ),
    Tool(
        name="slides_delete",
        description="Delete a Google Slides presentation",
        inputSchema={
            "type": "object",
            "properties": {
                "presentation_id": {
                    "type": "string",
                    "description": "Google Slides presentation ID to delete"
                }
            },
            "required": ["presentation_id"]
        }
    )
]


async def handle_slides_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle Slides tool execution.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        List of TextContent responses
    """
    try:
        if name == "slides_create":
            result = await slides_service.create_presentation(**arguments)
            return [TextContent(
                type="text",
                text=f"Created presentation: {result['title']}\n"
                     f"Presentation ID: {result['presentationId']}\n"
                     f"URL: https://docs.google.com/presentation/d/{result['presentationId']}"
            )]

        elif name == "slides_read":
            result = await slides_service.read_presentation(**arguments)
            slides_info = "\n".join([
                f"  Slide {i+1}: {slide['slide_id']} ({slide['page_elements']} elements)"
                for i, slide in enumerate(result['slides'])
            ])
            return [TextContent(
                type="text",
                text=f"Presentation: {result['title']}\n"
                     f"Presentation ID: {result['presentation_id']}\n"
                     f"Total slides: {result['slide_count']}\n\n"
                     f"Slides:\n{slides_info}"
            )]

        elif name == "slides_add_slide":
            result = await slides_service.add_slide(**arguments)
            return [TextContent(
                type="text",
                text=f"Successfully added slide to presentation: {arguments['presentation_id']}\n"
                     f"Replies: {len(result.get('replies', []))}"
            )]

        elif name == "slides_update":
            result = await slides_service.update_slide(**arguments)
            return [TextContent(
                type="text",
                text=f"Successfully updated slides in presentation: {arguments['presentation_id']}\n"
                     f"Replies: {len(result.get('replies', []))}"
            )]

        elif name == "slides_delete":
            await slides_service.delete_presentation(arguments['presentation_id'])
            return [TextContent(
                type="text",
                text=f"Successfully deleted presentation: {arguments['presentation_id']}"
            )]

        else:
            raise GoogleWorkspaceError(f"Unknown Slides tool: {name}")

    except GoogleWorkspaceError as e:
        logger.error(f"Slides tool error: {e.message}")
        return [TextContent(
            type="text",
            text=f"Error: {e.message}\nDetails: {e.details}"
        )]
