"""Entry point for running the Google Workspace MCP server as a module."""

import asyncio
from google_workspace_mcp.server_fastmcp import mcp


def main():
    """Entry point for console script."""
    # Import all tool modules to register their tools
    from google_workspace_mcp import tools  # noqa: F401

    # Run the FastMCP server
    mcp.run()


if __name__ == "__main__":
    main()
