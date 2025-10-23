"""MCP tools for Google Workspace services.

Tools are automatically registered with FastMCP when imported.
Each tool module uses @mcp.tool() decorators for registration.
"""

# Import all tool modules to register their tools with FastMCP
# The @mcp.tool() decorators in each module handle registration
from . import drive_tools  # noqa: F401

# TODO: Import remaining tool modules after refactoring:
# from . import docs_tools  # noqa: F401
# from . import sheets_tools  # noqa: F401
# from . import slides_tools  # noqa: F401
# from . import gmail_tools  # noqa: F401
# from . import forms_tools  # noqa: F401

__all__ = [
    'drive_tools',
    # 'docs_tools',
    # 'sheets_tools',
    # 'slides_tools',
    # 'gmail_tools',
    # 'forms_tools',
]
