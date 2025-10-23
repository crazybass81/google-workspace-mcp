#!/usr/bin/env python3
"""FastMCP-based MCP server implementation for Google Workspace integration.

This server provides comprehensive integration with Google Workspace services:
- Google Drive: File management, search, upload/download
- Google Docs: Document creation, reading, editing
- Google Sheets: Spreadsheet operations, data manipulation
- Google Slides: Presentation management, slide operations
- Google Forms: Form creation, editing, response collection
- Gmail: Email search, read, send, reply, label management

All tools follow MCP best practices with:
- Pydantic v2 input validation
- Comprehensive tool annotations
- Multiple response formats (JSON/Markdown)
- Proper pagination and character limits
- Actionable error messages
"""

from mcp.server.fastmcp import FastMCP

# Import all tool modules (these will register their tools with mcp)
from . import tools

# Initialize FastMCP server
mcp = FastMCP("google_workspace_mcp")


# Tool modules will use @mcp.tool() decorators to register themselves
# This is imported after mcp initialization so tools can register
__all__ = ['mcp']
