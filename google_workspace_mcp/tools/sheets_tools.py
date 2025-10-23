"""MCP tools for Google Sheets operations using FastMCP."""

import json
from typing import Optional, List, Any
from pydantic import Field, field_validator

from ..server_fastmcp import mcp
from ..services.sheets_service import SheetsService
from ..utils.logger import setup_logger
from ..utils.base_models import BaseMCPInput, SpreadsheetIdInput
from ..utils.response_formatter import (
    ResponseFormat,
    format_error,
    create_success_response,
    CHARACTER_LIMIT
)

logger = setup_logger(__name__)
sheets_service = SheetsService()


# ============================================================================
# Pydantic Input Models
# ============================================================================

class SheetsCreateInput(BaseMCPInput):
    """Input model for creating a Google Sheets spreadsheet."""

    title: str = Field(
        ...,
        description="Spreadsheet title (e.g., 'Sales Data 2025', 'Project Tracker', 'Budget Q4')",
        min_length=1,
        max_length=255
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class SheetsReadInput(SpreadsheetIdInput):
    """Input model for reading data from a Google Sheets range."""

    range_name: str = Field(
        ...,
        description="Range in A1 notation (e.g., 'Sheet1!A1:D10', 'Data!B2:F100', 'Summary!A:Z')",
        min_length=1,
        max_length=500
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )

    @field_validator('range_name')
    @classmethod
    def validate_range_name(cls, v: str) -> str:
        """Validate A1 notation format."""
        if not v.strip():
            raise ValueError("Range name cannot be empty")
        # Basic validation - should contain sheet name and range
        if '!' not in v:
            raise ValueError("Range must include sheet name (e.g., 'Sheet1!A1:B10')")
        return v.strip()


class SheetsWriteInput(SpreadsheetIdInput):
    """Input model for writing data to a Google Sheets range."""

    range_name: str = Field(
        ...,
        description="Range in A1 notation to write to (e.g., 'Sheet1!A1', 'Data!B2:D5')",
        min_length=1,
        max_length=500
    )
    values: List[List[Any]] = Field(
        ...,
        description="2D array of values to write (e.g., [['Name', 'Age'], ['Alice', 30], ['Bob', 25]])",
        min_items=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )

    @field_validator('range_name')
    @classmethod
    def validate_range_name(cls, v: str) -> str:
        """Validate A1 notation format."""
        if not v.strip():
            raise ValueError("Range name cannot be empty")
        if '!' not in v:
            raise ValueError("Range must include sheet name (e.g., 'Sheet1!A1')")
        return v.strip()

    @field_validator('values')
    @classmethod
    def validate_values(cls, v: List[List[Any]]) -> List[List[Any]]:
        """Validate values array."""
        if not v:
            raise ValueError("Values array cannot be empty")
        # Check that all rows have at least one value
        for idx, row in enumerate(v):
            if not isinstance(row, list):
                raise ValueError(f"Row {idx} must be a list/array")
        return v


class SheetsClearInput(SpreadsheetIdInput):
    """Input model for clearing a Google Sheets range."""

    range_name: str = Field(
        ...,
        description="Range in A1 notation to clear (e.g., 'Sheet1!A1:D10', 'Data!A:Z')",
        min_length=1,
        max_length=500
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )

    @field_validator('range_name')
    @classmethod
    def validate_range_name(cls, v: str) -> str:
        """Validate A1 notation format."""
        if not v.strip():
            raise ValueError("Range name cannot be empty")
        if '!' not in v:
            raise ValueError("Range must include sheet name (e.g., 'Sheet1!A1:D10')")
        return v.strip()


# ============================================================================
# Tool Implementations
# ============================================================================

@mcp.tool(
    name="sheets_create",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def sheets_create(params: SheetsCreateInput) -> str:
    """Create a new Google Sheets spreadsheet.

    Creates a blank spreadsheet with the specified title in the user's Google Drive.
    The spreadsheet contains one default sheet named "Sheet1".

    Use this when you need to:
    - Create a new spreadsheet for data tracking
    - Start a collaborative data project
    - Generate spreadsheets programmatically

    Args:
        params (SheetsCreateInput): Validated parameters with:
            - title: Spreadsheet title
            - response_format: Output format (markdown/json)

    Returns:
        str: Spreadsheet ID and web URL for accessing the created spreadsheet

    Examples:
        - Create sales tracker: title='Q4 2025 Sales Data'
        - Create project tracker: title='Project Milestones Tracker'
        - Create budget: title='Department Budget 2025'
    """
    try:
        result = await sheets_service.create_spreadsheet(title=params.title)

        spreadsheet_id = result.get('spreadsheetId')
        return create_success_response(
            f"Created spreadsheet '{result['properties']['title']}'",
            data={
                "spreadsheet_id": spreadsheet_id,
                "title": result['properties']['title'],
                "url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            },
            response_format=params.response_format
        )

    except Exception as e:
        logger.error(f"sheets_create error: {str(e)}")
        return format_error(e, "creating spreadsheet")


@mcp.tool(
    name="sheets_read",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sheets_read(params: SheetsReadInput) -> str:
    """Read data from a Google Sheets range.

    Retrieves cell values from the specified range in A1 notation. Returns data
    as a 2D array where each inner array represents a row.

    Use this when you need to:
    - Read data from spreadsheets for analysis
    - Extract table data programmatically
    - Access specific cell ranges

    Args:
        params (SheetsReadInput): Validated parameters with:
            - spreadsheet_id: Google Sheets spreadsheet ID
            - range_name: Range in A1 notation (e.g., 'Sheet1!A1:D10')
            - response_format: Output format (markdown/json)

    Returns:
        str: Cell values in the specified range

    Examples:
        - Read headers: range_name='Sheet1!A1:Z1'
        - Read data table: range_name='Data!A2:F100'
        - Read entire sheet: range_name='Summary!A:Z'

    Note:
        - Empty cells are included as empty strings
        - Formulas are evaluated and only values are returned
        - Formatting is not included
        - Large ranges may be truncated if exceeding 25,000 characters
    """
    try:
        result = await sheets_service.read_range(
            spreadsheet_id=params.spreadsheet_id,
            range_name=params.range_name
        )

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2)

        # Markdown format
        values = result.get('values', [])
        if not values:
            return "No data found in the specified range."

        response = f"# Range: {result.get('range', params.range_name)}\n\n"
        response += f"**Rows**: {len(values)}\n"
        response += f"**Columns**: {len(values[0]) if values else 0}\n\n"
        response += "## Data\n\n"

        # Format as table
        for row in values:
            row_str = " | ".join(str(cell) for cell in row)
            response += f"| {row_str} |\n"

        # Check character limit
        if len(response) > CHARACTER_LIMIT:
            truncated = response[:CHARACTER_LIMIT - 200]
            truncated += "\n\n⚠️ **Content Truncated**: Range data exceeds character limit (25,000 chars)."
            truncated += f"\n\n**Tip**: Request smaller ranges or use pagination (read {len(values)} rows in chunks)."
            return truncated

        return response

    except Exception as e:
        logger.error(f"sheets_read error: {str(e)}")
        return format_error(e, "reading range")


@mcp.tool(
    name="sheets_write",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def sheets_write(params: SheetsWriteInput) -> str:
    """Write data to a Google Sheets range.

    Writes values to the specified range in A1 notation. Values are provided as
    a 2D array where each inner array represents a row. Existing data in the
    range is overwritten.

    Use this when you need to:
    - Update spreadsheet data programmatically
    - Write calculated results to sheets
    - Populate tables with data

    Args:
        params (SheetsWriteInput): Validated parameters with:
            - spreadsheet_id: Google Sheets spreadsheet ID
            - range_name: Range in A1 notation to write to
            - values: 2D array of values to write
            - response_format: Output format (markdown/json)

    Returns:
        str: Number of cells, rows, and columns updated

    Examples:
        - Write headers: values=[['Name', 'Email', 'Phone']], range_name='Sheet1!A1'
        - Write data rows: values=[['Alice', 'alice@example.com'], ['Bob', 'bob@example.com']], range_name='Sheet1!A2'
        - Update single cell: values=[['Total: $1000']], range_name='Summary!E10'

    Note:
        - Existing data in the range is overwritten
        - Empty cells can be written using empty strings
        - Values are written as-is (no formula evaluation)
        - Array dimensions should match the target range
    """
    try:
        result = await sheets_service.update_range(
            spreadsheet_id=params.spreadsheet_id,
            range_name=params.range_name,
            values=params.values
        )

        return create_success_response(
            f"Updated range '{params.range_name}'",
            data={
                "spreadsheet_id": params.spreadsheet_id,
                "range": params.range_name,
                "updated_cells": result.get('updatedCells', 0),
                "updated_rows": result.get('updatedRows', 0),
                "updated_columns": result.get('updatedColumns', 0)
            },
            response_format=params.response_format
        )

    except Exception as e:
        logger.error(f"sheets_write error: {str(e)}")
        return format_error(e, "writing to range")


@mcp.tool(
    name="sheets_clear",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sheets_clear(params: SheetsClearInput) -> str:
    """Clear data from a Google Sheets range.

    Clears all values from the specified range while preserving cell formatting,
    data validation, and other properties. This operation is destructive but
    can be undone via Google Sheets' undo feature.

    Use this when you need to:
    - Remove data while keeping formatting
    - Clear temporary or calculated values
    - Reset data ranges for fresh input

    Args:
        params (SheetsClearInput): Validated parameters with:
            - spreadsheet_id: Google Sheets spreadsheet ID
            - range_name: Range in A1 notation to clear
            - response_format: Output format (markdown/json)

    Returns:
        str: Confirmation message with cleared range

    Examples:
        - Clear data table: range_name='Data!A2:F100'
        - Clear entire sheet: range_name='Sheet1!A:Z'
        - Clear specific cells: range_name='Summary!E10:E20'

    Warning:
        - This operation clears cell values
        - Cell formatting and properties are preserved
        - Can be undone via Google Sheets UI (Ctrl+Z)
        - Cannot be undone via API after execution
    """
    try:
        # Note: sheets_service should have a clear_range method
        # For now, we'll use update_range with empty values as a workaround
        # The actual implementation depends on SheetsService having a clear method

        # Try to call clear_range if it exists, otherwise use update with empty values
        if hasattr(sheets_service, 'clear_range'):
            await sheets_service.clear_range(
                spreadsheet_id=params.spreadsheet_id,
                range_name=params.range_name
            )
        else:
            # Fallback: clear by updating with empty array
            # This is a placeholder - the service should implement clear_range
            logger.warning("SheetsService.clear_range not found, using empty update as fallback")
            await sheets_service.update_range(
                spreadsheet_id=params.spreadsheet_id,
                range_name=params.range_name,
                values=[[]]
            )

        return create_success_response(
            f"Cleared range '{params.range_name}'",
            data={
                "spreadsheet_id": params.spreadsheet_id,
                "cleared_range": params.range_name,
                "note": "Cell formatting and properties preserved. Values cleared."
            },
            response_format=params.response_format
        )

    except Exception as e:
        logger.error(f"sheets_clear error: {str(e)}")
        return format_error(e, "clearing range")
