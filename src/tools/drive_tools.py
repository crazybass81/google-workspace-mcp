"""MCP tools for Google Drive operations."""

from typing import Any, Dict, List
from mcp.types import Tool, TextContent

from ..services.drive_service import DriveService
from ..utils.logger import setup_logger
from ..utils.error_handler import GoogleWorkspaceError

logger = setup_logger(__name__)

# Initialize Drive service
drive_service = DriveService()


# Tool definitions
DRIVE_TOOLS = [
    Tool(
        name="drive_search_files",
        description="Search for files and folders in Google Drive",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (file name contains)"
                },
                "folder_id": {
                    "type": "string",
                    "description": "Limit search to specific folder ID"
                },
                "file_type": {
                    "type": "string",
                    "description": "Filter by MIME type (e.g., 'application/pdf')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 100)",
                    "default": 100
                }
            }
        }
    ),
    Tool(
        name="drive_read_file",
        description="Read file content from Google Drive",
        inputSchema={
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "Google Drive file ID"
                },
                "mime_type": {
                    "type": "string",
                    "description": "Export MIME type for Google Docs files (e.g., 'text/plain', 'application/pdf')"
                }
            },
            "required": ["file_id"]
        }
    ),
    Tool(
        name="drive_create_file",
        description="Create a new file in Google Drive",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "File name"
                },
                "content": {
                    "type": "string",
                    "description": "File content",
                    "default": ""
                },
                "mime_type": {
                    "type": "string",
                    "description": "MIME type (default: 'text/plain')",
                    "default": "text/plain"
                },
                "folder_id": {
                    "type": "string",
                    "description": "Parent folder ID (optional)"
                }
            },
            "required": ["name"]
        }
    ),
    Tool(
        name="drive_update_file",
        description="Update an existing file in Google Drive",
        inputSchema={
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "Google Drive file ID"
                },
                "content": {
                    "type": "string",
                    "description": "New file content"
                },
                "name": {
                    "type": "string",
                    "description": "New file name"
                }
            },
            "required": ["file_id"]
        }
    ),
    Tool(
        name="drive_delete_file",
        description="Delete a file from Google Drive",
        inputSchema={
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "Google Drive file ID to delete"
                }
            },
            "required": ["file_id"]
        }
    ),
    Tool(
        name="drive_upload_file",
        description="Upload a local file to Google Drive",
        inputSchema={
            "type": "object",
            "properties": {
                "local_path": {
                    "type": "string",
                    "description": "Local file path to upload"
                },
                "name": {
                    "type": "string",
                    "description": "Name for uploaded file (optional, defaults to filename)"
                },
                "folder_id": {
                    "type": "string",
                    "description": "Parent folder ID (optional)"
                }
            },
            "required": ["local_path"]
        }
    ),
    Tool(
        name="drive_download_file",
        description="Download a file from Google Drive to local system",
        inputSchema={
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "Google Drive file ID"
                },
                "local_path": {
                    "type": "string",
                    "description": "Local path to save file"
                },
                "mime_type": {
                    "type": "string",
                    "description": "Export MIME type for Google Docs files"
                }
            },
            "required": ["file_id", "local_path"]
        }
    ),
    Tool(
        name="drive_list_shared_drives",
        description="List all shared drives (Team Drives) accessible to the user",
        inputSchema={
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 100)",
                    "default": 100
                }
            }
        }
    )
]


async def handle_drive_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle Drive tool execution.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        List of TextContent responses
    """
    try:
        if name == "drive_search_files":
            result = await drive_service.search_files(**arguments)
            return [TextContent(
                type="text",
                text=f"Found {len(result)} files:\n" +
                     "\n".join([f"- {f['name']} (ID: {f['id']}, Type: {f['mimeType']})"
                               for f in result])
            )]

        elif name == "drive_read_file":
            result = await drive_service.read_file(**arguments)
            return [TextContent(
                type="text",
                text=f"File: {result['metadata']['name']}\n"
                     f"Type: {result['metadata']['mimeType']}\n"
                     f"Modified: {result['metadata']['modifiedTime']}\n\n"
                     f"Content:\n{result['content']}"
            )]

        elif name == "drive_create_file":
            result = await drive_service.create_file(**arguments)
            return [TextContent(
                type="text",
                text=f"Created file: {result['name']}\n"
                     f"ID: {result['id']}\n"
                     f"Link: {result.get('webViewLink', 'N/A')}"
            )]

        elif name == "drive_update_file":
            result = await drive_service.update_file(**arguments)
            return [TextContent(
                type="text",
                text=f"Updated file: {result['name']}\n"
                     f"ID: {result['id']}\n"
                     f"Modified: {result['modifiedTime']}"
            )]

        elif name == "drive_delete_file":
            await drive_service.delete_file(arguments['file_id'])
            return [TextContent(
                type="text",
                text=f"Successfully deleted file: {arguments['file_id']}"
            )]

        elif name == "drive_upload_file":
            result = await drive_service.upload_file(**arguments)
            return [TextContent(
                type="text",
                text=f"Uploaded file: {result['name']}\n"
                     f"ID: {result['id']}\n"
                     f"Link: {result.get('webViewLink', 'N/A')}"
            )]

        elif name == "drive_download_file":
            result = await drive_service.download_file(**arguments)
            return [TextContent(
                type="text",
                text=f"Downloaded file to: {arguments['local_path']}\n"
                     f"Size: {result.get('size', 'unknown')} bytes"
            )]

        elif name == "drive_list_shared_drives":
            result = await drive_service.list_shared_drives(**arguments)
            return [TextContent(
                type="text",
                text=f"Found {len(result)} shared drives:\n" +
                     "\n".join([f"- {d['name']} (ID: {d['id']})" for d in result])
            )]

        else:
            raise GoogleWorkspaceError(f"Unknown Drive tool: {name}")

    except GoogleWorkspaceError as e:
        logger.error(f"Drive tool error: {e.message}")
        return [TextContent(
            type="text",
            text=f"Error: {e.message}\nDetails: {e.details}"
        )]
