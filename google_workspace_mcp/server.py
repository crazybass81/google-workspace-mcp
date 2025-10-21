#!/usr/bin/env python3
"""Main MCP server implementation for Google Workspace integration."""

import asyncio
from typing import Any, Dict, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from .utils.logger import setup_logger
from .utils.error_handler import GoogleWorkspaceError
from .tools import ALL_TOOLS, handle_drive_tool, handle_docs_tool, handle_sheets_tool, \
                   handle_slides_tool, handle_forms_tool, handle_gmail_tool

logger = setup_logger(__name__)

# Initialize MCP server
app = Server("google-workspace-mcp")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available MCP tools.

    Returns:
        List of Tool definitions
    """
    logger.info(f"Listing {len(ALL_TOOLS)} available tools")
    return ALL_TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent | ImageContent | EmbeddedResource]:
    """Execute a tool by name.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        List of content items

    Raises:
        GoogleWorkspaceError: If tool execution fails
    """
    logger.info(f"Calling tool: {name}")
    logger.debug(f"Arguments: {arguments}")

    try:
        # Route to appropriate handler
        if name.startswith("drive_"):
            return await handle_drive_tool(name, arguments)
        elif name.startswith("docs_"):
            return await handle_docs_tool(name, arguments)
        elif name.startswith("sheets_"):
            return await handle_sheets_tool(name, arguments)
        elif name.startswith("slides_"):
            return await handle_slides_tool(name, arguments)
        elif name.startswith("forms_"):
            return await handle_forms_tool(name, arguments)
        elif name.startswith("gmail_"):
            return await handle_gmail_tool(name, arguments)
        else:
            raise GoogleWorkspaceError(f"Unknown tool: {name}")

    except GoogleWorkspaceError as e:
        logger.error(f"Tool execution failed: {e.message}")
        return [
            TextContent(
                type="text",
                text=f"Error: {e.message}\nDetails: {e.details}"
            )
        ]
    except Exception as e:
        logger.exception(f"Unexpected error in tool {name}")
        return [
            TextContent(
                type="text",
                text=f"Unexpected error: {str(e)}"
            )
        ]


async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Google Workspace MCP Server")

    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.exception("Server error")
        raise
    finally:
        logger.info("Server stopped")


if __name__ == "__main__":
    asyncio.run(main())
