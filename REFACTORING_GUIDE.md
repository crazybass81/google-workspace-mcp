# Google Workspace MCP Refactoring Guide

## ✅ Completed Work

### Infrastructure (100% Complete)
- ✅ FastMCP server initialization (`server_fastmcp.py`)
- ✅ Common utilities (`utils/response_formatter.py`)
- ✅ Pydantic base models (`utils/base_models.py`)
- ✅ Updated `__main__.py` to use FastMCP
- ✅ Updated `tools/__init__.py` for FastMCP registration
- ✅ Fixed `.mcp.json` configuration (correct module path)

### Tools (Drive = 100%, Others = 0%)
- ✅ **Drive tools** (8/8): Fully refactored to MCP standards
  - Pydantic v2 input validation with comprehensive examples
  - Tool annotations (readOnlyHint, destructiveHint, idempotentHint, openWorldHint)
  - Response format options (JSON/Markdown)
  - Pagination metadata
  - Character limit handling
  - Actionable error messages

- ⏳ **Docs tools** (0/4): Template provided below
- ⏳ **Sheets tools** (0/4): Template provided below
- ⏳ **Slides tools** (0/4): Template provided below
- ⏳ **Gmail tools** (0/5): Template provided below
- ⏳ **Forms tools** (0/~4): Template provided below

---

## 🎯 How to Refactor Remaining Tools

### Step-by-Step Process

1. **Copy the template below** for the service you're refactoring
2. **Fill in the Pydantic models** based on existing inputSchema
3. **Implement tool functions** using `@mcp.tool()` decorator
4. **Add proper annotations** (readOnly, destructive, idempotent, openWorld)
5. **Test the tool** with `python3 -m google_workspace_mcp`
6. **Uncomment the import** in `tools/__init__.py`

### Example: Drive Tools Pattern

The completed `drive_tools.py` follows this pattern:

```python
"""MCP tools for [SERVICE] operations using FastMCP."""

import json
from typing import Optional
from pydantic import BaseModel, Field

from ..server_fastmcp import mcp
from ..services.[service]_service import [Service]Service
from ..utils.logger import setup_logger
from ..utils.base_models import BaseMCPInput, BaseListInput
from ..utils.response_formatter import (
    ResponseFormat,
    format_error,
    create_success_response,
    CHARACTER_LIMIT
)

logger = setup_logger(__name__)
[service]_service = [Service]Service()


# ============================================================================
# Pydantic Input Models
# ============================================================================

class [Tool]Input(BaseMCPInput):
    """Input model for [tool description]."""

    # Define fields with Field() for validation
    field_name: str = Field(
        ...,  # Required field
        description="Clear description with examples (e.g., 'value1', 'value2')",
        min_length=1,
        max_length=500,
        pattern=r'^[a-zA-Z0-9_-]+$'  # Optional regex
    )
    optional_field: Optional[str] = Field(
        default=None,
        description="Optional field description"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


# ============================================================================
# Tool Implementations
# ============================================================================

@mcp.tool(
    name="[service]_[action]_[resource]",
    annotations={
        "readOnlyHint": True,  # True if no modifications
        "destructiveHint": False,  # True if deletes data
        "idempotentHint": True,  # True if repeated calls = same result
        "openWorldHint": True  # True for external APIs
    }
)
async def [service]_[action]_[resource](params: [Tool]Input) -> str:
    """[One-line description of what this tool does].

    [Detailed explanation of purpose, use cases, and functionality]

    Use this when you need to:
    - [Use case 1]
    - [Use case 2]
    - [Use case 3]

    Args:
        params ([Tool]Input): Validated parameters with:
            - field_name: Description
            - optional_field: Description
            - response_format: Output format (markdown/json)

    Returns:
        str: [Description of return value format]

    Examples:
        - [Example 1]: field_name='value1'
        - [Example 2]: field_name='value2', optional_field='opt'
    """
    try:
        # Call service with validated parameters
        result = await [service]_service.[method_name](
            field_name=params.field_name,
            optional_field=params.optional_field
        )

        # Format response based on response_format
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2)

        # Markdown format
        return create_success_response(
            "Operation completed successfully",
            data=result,
            response_format=params.response_format
        )

    except Exception as e:
        logger.error(f"[service]_[action]_[resource] error: {str(e)}")
        return format_error(e, "performing operation")
```

---

## 📋 Templates for Remaining Tools

### Docs Tools Template

```python
"""MCP tools for Google Docs operations using FastMCP."""

import json
from typing import Optional
from pydantic import BaseModel, Field

from ..server_fastmcp import mcp
from ..services.docs_service import DocsService
from ..utils.logger import setup_logger
from ..utils.base_models import BaseMCPInput, DocumentIdInput
from ..utils.response_formatter import (
    ResponseFormat,
    format_error,
    create_success_response,
    CHARACTER_LIMIT
)

logger = setup_logger(__name__)
docs_service = DocsService()


# ============================================================================
# Pydantic Input Models
# ============================================================================

class DocsCreateInput(BaseMCPInput):
    """Input model for creating a Google Docs document."""

    title: str = Field(
        ...,
        description="Document title (e.g., 'Meeting Notes', 'Project Plan')",
        min_length=1,
        max_length=255
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class DocsReadInput(DocumentIdInput):
    """Input model for reading a document."""

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class DocsUpdateInput(DocumentIdInput):
    """Input model for updating document content."""

    text: str = Field(
        ...,
        description="Text content to insert into document",
        max_length=1000000
    )
    index: int = Field(
        default=1,
        description="Position to insert text (default: 1 = start)",
        ge=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


# ============================================================================
# Tool Implementations
# ============================================================================

@mcp.tool(
    name="docs_create",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def docs_create(params: DocsCreateInput) -> str:
    """Create a new Google Docs document.

    Creates a blank Google Docs document with the specified title.
    The document is created in the user's Drive.

    Args:
        params (DocsCreateInput): Document creation parameters

    Returns:
        str: Document ID and URL for the created document
    """
    try:
        result = await docs_service.create_document(title=params.title)

        return create_success_response(
            f"Created document '{result.get('title')}'",
            data={
                "document_id": result.get('documentId'),
                "url": f"https://docs.google.com/document/d/{result.get('documentId')}"
            },
            response_format=params.response_format
        )

    except Exception as e:
        logger.error(f"docs_create error: {str(e)}")
        return format_error(e, "creating document")


@mcp.tool(
    name="docs_read",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def docs_read(params: DocsReadInput) -> str:
    """Read content from a Google Docs document.

    Retrieves the complete text content of a Google Docs document.

    Args:
        params (DocsReadInput): Document ID to read

    Returns:
        str: Document title and full text content
    """
    try:
        result = await docs_service.read_document(document_id=params.document_id)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2)

        # Markdown format
        response = f"# Document: {result.get('title')}\n\n"
        response += f"**Document ID**: `{result.get('document_id')}`\n\n"
        response += f"## Content\n\n{result.get('content')}"

        # Check character limit
        if len(response) > CHARACTER_LIMIT:
            truncated = response[:CHARACTER_LIMIT - 200]
            truncated += "\n\n⚠️ **Content Truncated**: Document exceeds character limit."
            return truncated

        return response

    except Exception as e:
        logger.error(f"docs_read error: {str(e)}")
        return format_error(e, "reading document")


@mcp.tool(
    name="docs_update",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def docs_update(params: DocsUpdateInput) -> str:
    """Update content in a Google Docs document.

    Inserts text at the specified position in the document.

    Args:
        params (DocsUpdateInput): Update parameters

    Returns:
        str: Success confirmation
    """
    try:
        await docs_service.update_document(
            document_id=params.document_id,
            text=params.text,
            index=params.index
        )

        return create_success_response(
            f"Inserted text at index {params.index}",
            data={"document_id": params.document_id},
            response_format=params.response_format
        )

    except Exception as e:
        logger.error(f"docs_update error: {str(e)}")
        return format_error(e, "updating document")
```

### Sheets/Slides/Gmail/Forms Templates

Follow the same pattern as above:

1. **Import dependencies** (FastMCP, Pydantic, utilities)
2. **Define Pydantic input models** extending base models
3. **Implement tools** with `@mcp.tool()` decorator
4. **Add comprehensive docstrings** with use cases and examples
5. **Handle errors** with format_error()
6. **Support response formats** (JSON/Markdown)

---

## 🔧 Tool Annotations Reference

### readOnlyHint
- `True`: Tool does NOT modify data (searches, reads)
- `False`: Tool modifies data (creates, updates, deletes)

### destructiveHint
- `True`: Tool DELETES or irreversibly modifies data
- `False`: Tool is non-destructive

### idempotentHint
- `True`: Repeated calls produce same result (reads, idempotent updates)
- `False`: Each call produces different results (creates)

### openWorldHint
- `True`: Tool interacts with external systems (all Google Workspace tools)
- `False`: Tool only operates on local data

### Annotation Examples

```python
# Read operation
annotations={
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True
}

# Create operation
annotations={
    "readOnlyHint": False,
    "destructiveHint": False,
    "idempotentHint": False,
    "openWorldHint": True
}

# Delete operation
annotations={
    "readOnlyHint": False,
    "destructiveHint": True,
    "idempotentHint": True,
    "openWorldHint": True
}
```

---

## ✅ Testing Checklist

After refactoring each tool module:

1. **Syntax Check**: `python -m py_compile google_workspace_mcp/tools/[service]_tools.py`
2. **Import Test**: `python3 -c "from google_workspace_mcp.tools import [service]_tools"`
3. **Server Start**: `timeout 5s python3 -m google_workspace_mcp` (should start without errors)
4. **Uncomment Import**: In `tools/__init__.py`, uncomment the import line
5. **Full Test**: Test tool execution through MCP client

---

## 📊 Progress Tracking

| Service | Tools | Status | Notes |
|---------|-------|--------|-------|
| Drive | 8 | ✅ Complete | All tools refactored |
| Docs | 4 | ⏳ Template ready | Use template above |
| Sheets | 4 | ⏳ Template ready | Follow Docs pattern |
| Slides | 4 | ⏳ Template ready | Follow Docs pattern |
| Gmail | 5 | ⏳ Template ready | Follow Docs pattern |
| Forms | ~4 | ⏳ Template ready | Follow Docs pattern |

---

## 🚀 Quick Start for Next Steps

### 1. Refactor Docs Tools (Easiest)

```bash
# Create the file using template above
# Test it
python -m py_compile google_workspace_mcp/tools/docs_tools.py
python3 -c "from google_workspace_mcp.tools import docs_tools"

# Uncomment in tools/__init__.py
# from . import docs_tools  # noqa: F401

# Test server
timeout 5s python3 -m google_workspace_mcp
```

### 2. Repeat for Other Services

Follow the same pattern for Sheets, Slides, Gmail, and Forms.

### 3. Final Validation

Once all tools are refactored:
- Verify all imports work
- Test server starts successfully
- Validate against MCP standards checklist
- Test with Claude Code MCP client

---

## 📝 Notes

- **Drive tools are production-ready** and can be tested immediately
- **All infrastructure is in place** for remaining tools
- **Templates provide 80% of the code** - just fill in service-specific details
- **Estimated time per service**: 15-30 minutes following templates

---

## 🆘 Troubleshooting

### Import Errors
If you see import errors, ensure:
1. File is in `google_workspace_mcp/tools/` directory
2. File imports `from ..server_fastmcp import mcp`
3. All Pydantic models are defined before tool functions
4. Import is uncommented in `tools/__init__.py`

### Server Won't Start
Check:
1. All tool files have valid Python syntax
2. No circular imports
3. All dependencies are installed
4. OAuth credentials are configured

### Tool Not Showing Up
Verify:
1. Tool function has `@mcp.tool()` decorator
2. Tool module is imported in `tools/__init__.py`
3. Server was restarted after changes

---

*Last Updated: 2025-10-23*
*Drive Tools: ✅ Complete | Infrastructure: ✅ Complete | Remaining: 🔄 In Progress*
