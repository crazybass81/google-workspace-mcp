"""MCP tools for Google Sheets operations."""

from typing import Any, Dict, List
from mcp.types import Tool, TextContent

from ..services.sheets_service import SheetsService
from ..utils.logger import setup_logger
from ..utils.error_handler import GoogleWorkspaceError

logger = setup_logger(__name__)

# Initialize Sheets service
sheets_service = SheetsService()


# Tool definitions
SHEETS_TOOLS = [
    Tool(
        name="sheets_create",
        description="Create a new Google Sheets spreadsheet",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Spreadsheet title"
                }
            },
            "required": ["title"]
        }
    ),
    Tool(
        name="sheets_read",
        description="Read data from a Google Sheets range",
        inputSchema={
            "type": "object",
            "properties": {
                "spreadsheet_id": {
                    "type": "string",
                    "description": "Google Sheets spreadsheet ID"
                },
                "range_name": {
                    "type": "string",
                    "description": "Range in A1 notation (e.g., 'Sheet1!A1:D10')"
                }
            },
            "required": ["spreadsheet_id", "range_name"]
        }
    ),
    Tool(
        name="sheets_update",
        description="Update data in a Google Sheets range",
        inputSchema={
            "type": "object",
            "properties": {
                "spreadsheet_id": {
                    "type": "string",
                    "description": "Google Sheets spreadsheet ID"
                },
                "range_name": {
                    "type": "string",
                    "description": "Range in A1 notation (e.g., 'Sheet1!A1:D10')"
                },
                "values": {
                    "type": "array",
                    "description": "2D array of values to write",
                    "items": {
                        "type": "array",
                        "items": {}
                    }
                }
            },
            "required": ["spreadsheet_id", "range_name", "values"]
        }
    ),
    Tool(
        name="sheets_delete",
        description="Delete a Google Sheets spreadsheet",
        inputSchema={
            "type": "object",
            "properties": {
                "spreadsheet_id": {
                    "type": "string",
                    "description": "Google Sheets spreadsheet ID to delete"
                }
            },
            "required": ["spreadsheet_id"]
        }
    ),
    Tool(
        name="sheets_batch_update",
        description="Perform batch update operations on a spreadsheet",
        inputSchema={
            "type": "object",
            "properties": {
                "spreadsheet_id": {
                    "type": "string",
                    "description": "Google Sheets spreadsheet ID"
                },
                "requests": {
                    "type": "array",
                    "description": "Array of update requests",
                    "items": {
                        "type": "object"
                    }
                }
            },
            "required": ["spreadsheet_id", "requests"]
        }
    )
]


async def handle_sheets_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle Sheets tool execution.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        List of TextContent responses
    """
    try:
        if name == "sheets_create":
            result = await sheets_service.create_spreadsheet(**arguments)
            return [TextContent(
                type="text",
                text=f"Created spreadsheet: {result['properties']['title']}\n"
                     f"Spreadsheet ID: {result['spreadsheetId']}\n"
                     f"URL: https://docs.google.com/spreadsheets/d/{result['spreadsheetId']}"
            )]

        elif name == "sheets_read":
            result = await sheets_service.read_range(**arguments)
            rows_text = "\n".join([
                "\t".join(str(cell) for cell in row)
                for row in result['values']
            ])
            return [TextContent(
                type="text",
                text=f"Range: {result['range']}\n"
                     f"Rows: {len(result['values'])}\n\n"
                     f"Data:\n{rows_text}"
            )]

        elif name == "sheets_update":
            result = await sheets_service.update_range(**arguments)
            return [TextContent(
                type="text",
                text=f"Successfully updated range: {arguments['range_name']}\n"
                     f"Updated cells: {result.get('updatedCells', 0)}\n"
                     f"Updated rows: {result.get('updatedRows', 0)}\n"
                     f"Updated columns: {result.get('updatedColumns', 0)}"
            )]

        elif name == "sheets_delete":
            await sheets_service.delete_spreadsheet(arguments['spreadsheet_id'])
            return [TextContent(
                type="text",
                text=f"Successfully deleted spreadsheet: {arguments['spreadsheet_id']}"
            )]

        elif name == "sheets_batch_update":
            result = await sheets_service.batch_update(**arguments)
            return [TextContent(
                type="text",
                text=f"Successfully performed batch update on spreadsheet: {arguments['spreadsheet_id']}\n"
                     f"Replies: {len(result.get('replies', []))}"
            )]

        else:
            raise GoogleWorkspaceError(f"Unknown Sheets tool: {name}")

    except GoogleWorkspaceError as e:
        logger.error(f"Sheets tool error: {e.message}")
        return [TextContent(
            type="text",
            text=f"Error: {e.message}\nDetails: {e.details}"
        )]
