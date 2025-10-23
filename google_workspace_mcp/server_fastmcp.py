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

# Initialize FastMCP server
mcp = FastMCP("google_workspace_mcp")

# NOTE: Tool modules are imported in __main__.py to avoid circular imports
# Each tool module imports this mcp instance and uses @mcp.tool() decorators

__all__ = ['mcp']
