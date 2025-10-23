"""MCP tools for Google Slides operations using FastMCP."""

import json
from typing import Optional
from pydantic import Field

from ..server_fastmcp import mcp
from ..services.slides_service import SlidesService
from ..utils.logger import setup_logger
from ..utils.base_models import BaseMCPInput, PresentationIdInput
from ..utils.response_formatter import (
    ResponseFormat,
    format_error,
    create_success_response,
    CHARACTER_LIMIT
)

logger = setup_logger(__name__)
slides_service = SlidesService()


# ============================================================================
# Pydantic Input Models
# ============================================================================

class SlidesCreateInput(BaseMCPInput):
    """Input model for creating a Google Slides presentation."""

    title: str = Field(
        ...,
        description="Presentation title (e.g., 'Q4 2025 Review', 'Project Kickoff', 'Sales Presentation')",
        min_length=1,
        max_length=255
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class SlidesReadInput(PresentationIdInput):
    """Input model for reading a Google Slides presentation."""

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class SlidesAddSlideInput(PresentationIdInput):
    """Input model for adding a slide to a presentation."""

    slide_index: Optional[int] = Field(
        default=None,
        description="Position to insert slide (0 = beginning, None = end)",
        ge=0
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class SlidesDeleteSlideInput(PresentationIdInput):
    """Input model for deleting a slide from a presentation."""

    slide_id: str = Field(
        ...,
        description="Slide object ID to delete (e.g., 'g123abc456def')",
        min_length=1,
        max_length=200
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


# ============================================================================
# Tool Implementations
# ============================================================================

@mcp.tool(
    name="slides_create",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def slides_create(params: SlidesCreateInput) -> str:
    """Create a new Google Slides presentation.

    Creates a blank presentation with the specified title in the user's Google Drive.
    The presentation contains one default blank slide.

    Use this when you need to:
    - Create a new presentation for meetings or reports
    - Start a collaborative slide deck
    - Generate presentations programmatically

    Args:
        params (SlidesCreateInput): Validated parameters with:
            - title: Presentation title
            - response_format: Output format (markdown/json)

    Returns:
        str: Presentation ID and web URL for accessing the created presentation

    Examples:
        - Create quarterly review: title='Q4 2025 Business Review'
        - Create project deck: title='Project Alpha Kickoff'
        - Create sales pitch: title='Product Demo 2025'
    """
    try:
        result = await slides_service.create_presentation(title=params.title)

        presentation_id = result.get('presentationId')
        return create_success_response(
            f"Created presentation '{result.get('title')}'",
            data={
                "presentation_id": presentation_id,
                "title": result.get('title'),
                "url": f"https://docs.google.com/presentation/d/{presentation_id}"
            },
            response_format=params.response_format
        )

    except Exception as e:
        logger.error(f"slides_create error: {str(e)}")
        return format_error(e, "creating presentation")


@mcp.tool(
    name="slides_read",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def slides_read(params: SlidesReadInput) -> str:
    """Read content from a Google Slides presentation.

    Retrieves presentation metadata and text content from all slides. This extracts
    text from slide elements but does not include images, shapes, or formatting.

    Use this when you need to:
    - Read presentation content for analysis
    - Extract text from slides
    - Review presentation structure

    Args:
        params (SlidesReadInput): Validated parameters with:
            - presentation_id: Google Slides presentation ID
            - response_format: Output format (markdown/json)

    Returns:
        str: Presentation title, slide count, and text content from all slides

    Examples:
        - Read quarterly review: presentation_id='1A2B3C4D5E6F'
        - Extract presentation content: presentation_id='9X8Y7Z6W5V4U'

    Note:
        - Only text content is extracted
        - Images and shapes are not included
        - Formatting is not preserved
        - Large presentations may be truncated if exceeding 25,000 characters
    """
    try:
        result = await slides_service.read_presentation(presentation_id=params.presentation_id)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2)

        # Markdown format
        response = f"# Presentation: {result.get('title', 'Untitled')}\n\n"
        response += f"**Presentation ID**: `{result.get('presentation_id')}`\n"
        response += f"**Slides**: {result.get('slide_count', 0)}\n\n"

        # Add content from each slide
        content = result.get('content', '')
        if content:
            response += f"## Content\n\n{content}"
        else:
            response += "## Content\n\n_No text content found in slides._"

        # Check character limit
        if len(response) > CHARACTER_LIMIT:
            truncated = response[:CHARACTER_LIMIT - 200]
            truncated += "\n\n⚠️ **Content Truncated**: Presentation content exceeds character limit (25,000 chars)."
            truncated += "\n\n**Tip**: Consider reading individual slides or reducing content length."
            return truncated

        return response

    except Exception as e:
        logger.error(f"slides_read error: {str(e)}")
        return format_error(e, "reading presentation")


@mcp.tool(
    name="slides_add_slide",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def slides_add_slide(params: SlidesAddSlideInput) -> str:
    """Add a new slide to a Google Slides presentation.

    Inserts a blank slide at the specified position in the presentation.
    If no position is specified, the slide is added at the end.

    Use this when you need to:
    - Add more slides to a presentation
    - Insert slides at specific positions
    - Build presentations programmatically

    Args:
        params (SlidesAddSlideInput): Validated parameters with:
            - presentation_id: Google Slides presentation ID
            - slide_index: Position to insert (0 = beginning, None = end)
            - response_format: Output format (markdown/json)

    Returns:
        str: Slide ID and position of the newly added slide

    Examples:
        - Add slide at end: presentation_id='1A2B3C'
        - Insert at beginning: presentation_id='1A2B3C', slide_index=0
        - Insert after 3rd slide: presentation_id='1A2B3C', slide_index=3

    Note:
        - New slide is created with default blank layout
        - Slide index is 0-based (0 = first slide)
        - If index exceeds slide count, slide is added at end
    """
    try:
        result = await slides_service.add_slide(
            presentation_id=params.presentation_id,
            slide_index=params.slide_index
        )

        return create_success_response(
            f"Added slide to presentation",
            data={
                "presentation_id": params.presentation_id,
                "slide_id": result.get('slide_id'),
                "slide_index": result.get('slide_index', 'end')
            },
            response_format=params.response_format
        )

    except Exception as e:
        logger.error(f"slides_add_slide error: {str(e)}")
        return format_error(e, "adding slide")


@mcp.tool(
    name="slides_delete_slide",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def slides_delete_slide(params: SlidesDeleteSlideInput) -> str:
    """Delete a slide from a Google Slides presentation.

    ⚠️ WARNING: This operation permanently removes the slide from the presentation.
    The deletion can be undone via Google Slides' undo feature (Ctrl+Z) immediately
    after, but cannot be undone via API.

    Use this when you need to:
    - Remove obsolete or incorrect slides
    - Clean up presentation structure
    - Manage slide lifecycle programmatically

    Args:
        params (SlidesDeleteSlideInput): Validated parameters with:
            - presentation_id: Google Slides presentation ID
            - slide_id: Slide object ID to delete
            - response_format: Output format (markdown/json)

    Returns:
        str: Confirmation message with deleted slide ID

    Examples:
        - Delete specific slide: slide_id='g123abc456def'

    Warning:
        - Slide is permanently removed from presentation
        - Can be undone via Slides UI immediately (Ctrl+Z)
        - Cannot be undone via API after execution
        - To find slide IDs, use slides_read tool first

    Note:
        - Slide object IDs can be obtained from slides_read output
        - Deleting the last remaining slide may cause errors
        - Consider the presentation structure before deletion
    """
    try:
        await slides_service.delete_slide(
            presentation_id=params.presentation_id,
            slide_id=params.slide_id
        )

        return create_success_response(
            f"Deleted slide with ID: {params.slide_id}",
            data={
                "presentation_id": params.presentation_id,
                "deleted_slide_id": params.slide_id,
                "note": "Slide permanently deleted. Can be undone via Slides UI (Ctrl+Z) immediately after deletion."
            },
            response_format=params.response_format
        )

    except Exception as e:
        logger.error(f"slides_delete_slide error: {str(e)}")
        return format_error(e, "deleting slide")
