"""Entry point for running the Google Workspace MCP server as a module."""

import asyncio
from google_workspace_mcp.server import main as server_main


def main():
    """Entry point for console script."""
    asyncio.run(server_main())


if __name__ == "__main__":
    main()
