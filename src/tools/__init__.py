"""MCP tools for Google Workspace services."""

from .drive_tools import DRIVE_TOOLS, handle_drive_tool
from .docs_tools import DOCS_TOOLS, handle_docs_tool
from .sheets_tools import SHEETS_TOOLS, handle_sheets_tool
from .slides_tools import SLIDES_TOOLS, handle_slides_tool
from .forms_tools import FORMS_TOOLS, handle_forms_tool
from .gmail_tools import GMAIL_TOOLS, handle_gmail_tool

# Collect all tools
ALL_TOOLS = (
    DRIVE_TOOLS +
    DOCS_TOOLS +
    SHEETS_TOOLS +
    SLIDES_TOOLS +
    FORMS_TOOLS +
    GMAIL_TOOLS
)

__all__ = [
    'ALL_TOOLS',
    'DRIVE_TOOLS', 'handle_drive_tool',
    'DOCS_TOOLS', 'handle_docs_tool',
    'SHEETS_TOOLS', 'handle_sheets_tool',
    'SLIDES_TOOLS', 'handle_slides_tool',
    'FORMS_TOOLS', 'handle_forms_tool',
    'GMAIL_TOOLS', 'handle_gmail_tool'
]
