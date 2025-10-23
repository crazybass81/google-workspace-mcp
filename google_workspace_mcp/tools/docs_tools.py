"""MCP tools for Google Docs operations using FastMCP."""

import json
from typing import Optional
from pydantic import Field

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
        description="Document title (e.g., 'Meeting Notes', 'Project Plan', 'Q1 Report')",
        min_length=1,
        max_length=255
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class DocsReadInput(DocumentIdInput):
    """Input model for reading a Google Docs document."""

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class DocsUpdateInput(DocumentIdInput):
    """Input model for updating Google Docs document content."""

    text: str = Field(
        ...,
        description="Text content to insert into the document",
        max_length=1000000  # 1MB limit
    )
    index: int = Field(
        default=1,
        description="Position to insert text (1 = start of document, higher values = later positions)",
        ge=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class DocsDeleteInput(DocumentIdInput):
    """Input model for deleting a Google Docs document."""

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
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

    Creates a blank Google Docs document with the specified title in the user's
    Google Drive. The document is created empty and can be edited later using
    the docs_update tool.

    Use this when you need to:
    - Create a new document for notes or reports
    - Start a collaborative document
    - Generate documentation programmatically

    Args:
        params (DocsCreateInput): Validated parameters with:
            - title: Document title
            - response_format: Output format (markdown/json)

    Returns:
        str: Document ID and web URL for accessing the created document

    Examples:
        - Create meeting notes: title='Team Meeting Notes - 2025-10-23'
        - Create project plan: title='Q4 2025 Project Plan'
        - Create report: title='Monthly Sales Report'
    """
    try:
        result = await docs_service.create_document(title=params.title)

        document_id = result.get('documentId')
        return create_success_response(
            f"Created document '{result.get('title')}'",
            data={
                "document_id": document_id,
                "title": result.get('title'),
                "url": f"https://docs.google.com/document/d/{document_id}"
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

    Retrieves the complete text content of a Google Docs document. This extracts
    all text from the document, preserving paragraph structure but removing formatting.

    Use this when you need to:
    - Read document content for analysis
    - Extract text for processing
    - Review document contents programmatically

    Args:
        params (DocsReadInput): Validated parameters with:
            - document_id: Google Docs document ID
            - response_format: Output format (markdown/json)

    Returns:
        str: Document title and full text content

    Examples:
        - Read meeting notes: document_id='1A2B3C4D5E6F'
        - Extract report content: document_id='9X8Y7Z6W5V4U'

    Note:
        - Content exceeding 25,000 characters will be truncated
        - Formatting (bold, italic, etc.) is not preserved
        - Images and tables are not included in text extraction
    """
    try:
        result = await docs_service.read_document(document_id=params.document_id)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2)

        # Markdown format
        response = f"# Document: {result.get('title', 'Untitled')}\n\n"
        response += f"**Document ID**: `{result.get('document_id')}`\n\n"
        response += f"## Content\n\n{result.get('content', '')}"

        # Check character limit
        if len(response) > CHARACTER_LIMIT:
            truncated = response[:CHARACTER_LIMIT - 200]
            truncated += "\n\n⚠️ **Content Truncated**: Document content exceeds character limit (25,000 chars)."
            truncated += "\n\n**Tip**: Consider breaking the document into smaller sections or use pagination."
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

    Inserts text at the specified position in the document. By default, text is
    inserted at the beginning (index 1). To append to the end, use a large index value.

    Use this when you need to:
    - Add content to an existing document
    - Programmatically write to documents
    - Append notes or updates

    Args:
        params (DocsUpdateInput): Validated parameters with:
            - document_id: Google Docs document ID
            - text: Text content to insert
            - index: Position to insert (1 = start, default)
            - response_format: Output format (markdown/json)

    Returns:
        str: Success confirmation with document ID

    Examples:
        - Insert at beginning: document_id='1A2B3C', text='# Header\\n\\nContent', index=1
        - Append content: document_id='1A2B3C', text='\\n\\nAppendix', index=999999

    Note:
        - Index 1 inserts at the very beginning of the document
        - Text formatting must use plain text (Markdown-like syntax may not render)
        - Existing content is shifted, not overwritten
    """
    try:
        await docs_service.update_document(
            document_id=params.document_id,
            text=params.text,
            index=params.index
        )

        return create_success_response(
            f"Inserted {len(params.text)} characters at index {params.index}",
            data={
                "document_id": params.document_id,
                "text_length": len(params.text),
                "index": params.index
            },
            response_format=params.response_format
        )

    except Exception as e:
        logger.error(f"docs_update error: {str(e)}")
        return format_error(e, "updating document")


@mcp.tool(
    name="docs_delete",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def docs_delete(params: DocsDeleteInput) -> str:
    """Delete a Google Docs document.

    ⚠️ WARNING: This operation moves the document to trash. The document can be
    restored from Google Drive trash within 30 days, after which it is permanently deleted.

    Use this when you need to:
    - Remove obsolete documents
    - Clean up temporary files
    - Manage document lifecycle

    Args:
        params (DocsDeleteInput): Validated parameters with:
            - document_id: Google Docs document ID
            - response_format: Output format (markdown/json)

    Returns:
        str: Confirmation message with document ID

    Examples:
        - Delete temp document: document_id='1A2B3C4D5E6F'
        - Remove draft: document_id='9X8Y7Z6W5V4U'

    Warning:
        - Document is moved to trash, not immediately deleted
        - Can be restored from trash within 30 days
        - After 30 days, deletion is permanent
    """
    try:
        await docs_service.delete_document(document_id=params.document_id)

        return create_success_response(
            f"Deleted document with ID: {params.document_id}",
            data={
                "document_id": params.document_id,
                "note": "Document moved to trash. Can be restored from Google Drive trash within 30 days."
            },
            response_format=params.response_format
        )

    except Exception as e:
        logger.error(f"docs_delete error: {str(e)}")
        return format_error(e, "deleting document")
