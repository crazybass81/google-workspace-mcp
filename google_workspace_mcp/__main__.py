"""Entry point for running the Google Workspace MCP server as a module."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.server import main

if __name__ == "__main__":
    asyncio.run(main())
