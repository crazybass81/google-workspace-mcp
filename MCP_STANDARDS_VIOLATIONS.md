# MCP Standards Violations Report

## Executive Summary

The `google-workspace-mcp` repository contains multiple violations of MCP (Model Context Protocol) standards for Python implementations. This document outlines all identified issues and provides recommendations for bringing the codebase into compliance with MCP best practices.

---

## Critical Issues

### 1. ❌ Not Using FastMCP Framework

**Current Implementation:**
```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("google-workspace-mcp")

@app.list_tools()
async def list_tools() -> List[Tool]:
    return ALL_TOOLS

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]):
    # Manual routing logic
```

**MCP Standard:**
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("google_workspace_mcp")

@mcp.tool(name="drive_search_files", annotations={...})
async def drive_search_files(params: DriveSearchInput) -> str:
    # Implementation with automatic schema generation
```

**Impact:**
- Missing automatic description and inputSchema generation
- Manual tool registration is error-prone
- No integration with Pydantic for input validation
- Increased maintenance burden

**Files Affected:**
- `google_workspace_mcp/server.py`

---

### 2. ❌ No Pydantic Input Validation

**Current Implementation:**
```python
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
            # ... more properties
        }
    }
)
```

**MCP Standard:**
```python
from pydantic import BaseModel, Field, ConfigDict

class DriveSearchInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    query: Optional[str] = Field(
        default=None,
        description="Search query for file name (e.g., 'budget report', '*.pdf')",
        max_length=500
    )
    folder_id: Optional[str] = Field(
        default=None,
        description="Limit search to specific folder ID (e.g., '1A2B3C4D5E')",
        pattern=r'^[a-zA-Z0-9_-]+$'
    )
    file_type: Optional[str] = Field(
        default=None,
        description="Filter by MIME type (e.g., 'application/pdf', 'image/jpeg')"
    )
    max_results: int = Field(
        default=100,
        description="Maximum number of results to return",
        ge=1,
        le=1000
    )
```

**Impact:**
- No runtime input validation
- No type safety
- No field constraints (min/max length, ranges, patterns)
- No automatic whitespace trimming
- Missing comprehensive examples in descriptions
- Potential security vulnerabilities from unvalidated input

**Files Affected:**
- All files in `google_workspace_mcp/tools/`:
  - `drive_tools.py` (8 tools)
  - `docs_tools.py` (3 tools)
  - `sheets_tools.py` (4 tools)
  - `slides_tools.py` (4 tools)
  - `forms_tools.py` (tools count TBD)
  - `gmail_tools.py` (5 tools)

---

### 3. ❌ Missing Tool Annotations

**Current Implementation:**
```python
Tool(
    name="drive_search_files",
    description="Search for files and folders in Google Drive",
    inputSchema={...}
    # No annotations!
)
```

**MCP Standard:**
```python
@mcp.tool(
    name="drive_search_files",
    annotations={
        "readOnlyHint": True,      # Does not modify environment
        "destructiveHint": False,   # Not destructive
        "idempotentHint": True,     # Same result on repeated calls
        "openWorldHint": True       # Interacts with external system (Google Drive)
    }
)
```

**Impact:**
- LLMs cannot determine if tools are safe to execute
- No indication of tool side effects
- Missing safety metadata for execution planning
- Reduced transparency in tool behavior

**Required Annotations per Tool:**
- `drive_search_files`: readOnly=True, destructive=False, idempotent=True, openWorld=True
- `drive_read_file`: readOnly=True, destructive=False, idempotent=True, openWorld=True
- `drive_create_file`: readOnly=False, destructive=False, idempotent=False, openWorld=True
- `drive_update_file`: readOnly=False, destructive=False, idempotent=True, openWorld=True
- `drive_delete_file`: readOnly=False, destructive=True, idempotent=True, openWorld=True
- Similar annotations needed for all other tools

**Files Affected:**
- All tool definition files

---

### 4. ❌ Incorrect Package Configuration

**Issue in `.mcp.json`:**
```json
{
  "mcpServers": {
    "google-workspace": {
      "command": "/usr/local/bin/python3",
      "args": ["-m", "src.server"],  // ❌ WRONG MODULE PATH
      "cwd": "/Users/t/google-workspace-mcp",
      "env": {
        "PYTHONPATH": "/Users/t/google-workspace-mcp"
      }
    }
  }
}
```

**Correct Configuration:**
```json
{
  "mcpServers": {
    "google-workspace": {
      "command": "/usr/local/bin/python3",
      "args": ["-m", "google_workspace_mcp"],  // ✅ CORRECT
      "cwd": "/Users/t/google-workspace-mcp"
    }
  }
}
```

**Issue in README.md** (line 92):
```bash
# ❌ WRONG
python3 -m src.server

# ✅ CORRECT
python3 -m google_workspace_mcp
```

**Impact:**
- Server cannot be launched with documented commands
- Configuration file points to non-existent module
- User confusion and setup failures

**Files Affected:**
- `.mcp.json`
- `README.md`

---

### 5. ⚠️ Missing Response Format Options

**Current Implementation:**
- All tools return hardcoded Markdown-style text
- No `response_format` parameter
- No JSON output option

**MCP Standard:**
```python
from enum import Enum

class ResponseFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"

class DriveSearchInput(BaseModel):
    # ... other fields
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )
```

**Impact:**
- Cannot provide machine-readable structured output
- Limited flexibility for programmatic processing
- Reduced usefulness for automation workflows

**Files Affected:**
- All tool implementation functions

---

### 6. ⚠️ Missing Pagination Metadata

**Current Implementation:**
```python
return [TextContent(
    type="text",
    text=f"Found {len(result)} files:\n" + ...
)]
```

**MCP Standard:**
```python
response = {
    "total": total_count,
    "count": len(results),
    "offset": params.offset,
    "items": results,
    "has_more": has_more,
    "next_offset": next_offset if has_more else None
}
```

**Impact:**
- No indication if more results exist
- Cannot efficiently paginate through large result sets
- Missing total count information

**Files Affected:**
- All tools that return lists (search, list operations)

---

### 7. ⚠️ Missing Character Limit Handling

**Current Implementation:**
- No CHARACTER_LIMIT constant defined
- No truncation logic
- Could return overwhelming amounts of data

**MCP Standard:**
```python
CHARACTER_LIMIT = 25000

if len(result_text) > CHARACTER_LIMIT:
    # Truncate and provide guidance
    response["truncated"] = True
    response["truncation_message"] = (
        f"Response truncated. Use 'limit' and 'offset' parameters "
        f"or add filters to reduce results."
    )
```

**Impact:**
- Potential context overflow
- Poor UX with very large results
- No guidance on how to reduce result size

**Files Affected:**
- All tool implementation functions

---

### 8. ⚠️ Tool Descriptions Not Comprehensive

**Current Example:**
```python
description="Search for files and folders in Google Drive"
```

**MCP Standard:**
```python
'''Search for files and folders in Google Drive with flexible filtering.

This tool searches across all accessible Google Drive files and folders using
query-based matching. It supports filtering by folder, MIME type, and result limits.
Use this when you need to find specific files, explore folder contents, or discover
documents by name pattern.

Args:
    params (DriveSearchInput): Validated search parameters containing:
        - query (Optional[str]): Search query for file name matching
        - folder_id (Optional[str]): Limit search to specific folder
        - file_type (Optional[str]): Filter by MIME type
        - max_results (int): Maximum number of results (1-1000)

Returns:
    str: Formatted search results with file names, IDs, types, and links

Examples:
    - Find PDFs: file_type='application/pdf'
    - Search in folder: folder_id='1A2B3C'
    - Limit results: max_results=10
'''
```

**Impact:**
- LLMs have less context for proper tool usage
- Missing examples and parameter details
- Reduced tool discovery and correct usage

**Files Affected:**
- All tool functions

---

## Refactoring Priority

### P0 - Critical (Must Fix)
1. Migrate to FastMCP framework
2. Implement Pydantic input validation models
3. Fix `.mcp.json` and README module paths
4. Add tool annotations

### P1 - Important (Should Fix)
5. Add response format options (JSON/Markdown)
6. Implement pagination metadata
7. Add character limit handling

### P2 - Enhancement (Nice to Have)
8. Enhance tool descriptions with examples

---

## Estimated Effort

- **P0 Critical Issues**: 8-12 hours
  - FastMCP migration: 3-4 hours
  - Pydantic models (24+ tools): 4-6 hours
  - Tool annotations: 1-2 hours

- **P1 Important Issues**: 4-6 hours
  - Response formats: 2-3 hours
  - Pagination/truncation: 2-3 hours

- **P2 Enhancements**: 2-3 hours
  - Documentation: 2-3 hours

**Total**: 14-21 hours

---

## Recommendations

1. **Start with FastMCP Migration**: This is the foundation for all other improvements
2. **Batch Process Tools**: Refactor similar tools together (all Drive tools, then Docs, etc.)
3. **Test Incrementally**: Validate each service's tools before moving to the next
4. **Update Documentation**: Keep README and examples in sync with changes
5. **Add Quality Checklist**: Use the Python MCP Server Quality Checklist to verify compliance

---

## Files Requiring Changes

### Critical Changes:
- `google_workspace_mcp/server.py` - FastMCP migration
- `google_workspace_mcp/__main__.py` - Update if needed
- `.mcp.json` - Fix module path
- `README.md` - Fix commands and examples
- All tool files in `google_workspace_mcp/tools/`:
  - `drive_tools.py`
  - `docs_tools.py`
  - `sheets_tools.py`
  - `slides_tools.py`
  - `forms_tools.py`
  - `gmail_tools.py`

### Dependency Changes:
- `pyproject.toml` - May need FastMCP dependency verification
- `requirements.txt` - Update if needed

---

## Next Steps

1. ✅ Review this violations report
2. ⏳ Create detailed refactoring plan with task breakdown
3. ⏳ Implement P0 critical fixes
4. ⏳ Test with MCP client (Claude Code)
5. ⏳ Implement P1 important improvements
6. ⏳ Final quality check against MCP standards

---

*Report Generated: 2025-10-23*
*MCP Standards Version: Latest (FastMCP-based)*
