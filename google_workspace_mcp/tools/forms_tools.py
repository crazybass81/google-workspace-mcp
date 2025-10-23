"""MCP tools for Google Forms operations using FastMCP."""

import json
from typing import Optional, List, Any, Dict
from pydantic import Field, field_validator

from ..server_fastmcp import mcp
from ..services.forms_service import FormsService
from ..utils.logger import setup_logger
from ..utils.base_models import BaseMCPInput, FormIdInput
from ..utils.response_formatter import (
    ResponseFormat,
    format_error,
    create_success_response,
    CHARACTER_LIMIT
)

logger = setup_logger(__name__)
forms_service = FormsService()


# ============================================================================
# Pydantic Input Models
# ============================================================================

class FormsCreateInput(BaseMCPInput):
    """Input model for creating a Google Form."""

    title: str = Field(
        ...,
        description="Form title (e.g., 'Customer Feedback Survey', 'Event Registration', 'Quiz 2025')",
        min_length=1,
        max_length=255
    )
    document_title: Optional[str] = Field(
        default=None,
        description="Document title (optional, defaults to form title)",
        max_length=255
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class FormsReadInput(FormIdInput):
    """Input model for reading a Google Form."""

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class FormsUpdateInput(FormIdInput):
    """Input model for updating a Google Form."""

    requests: List[Dict[str, Any]] = Field(
        ...,
        description="Array of batch update requests following Google Forms API format",
        min_items=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )

    @field_validator('requests')
    @classmethod
    def validate_requests(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate requests array."""
        if not v:
            raise ValueError("Requests array cannot be empty")
        for idx, req in enumerate(v):
            if not isinstance(req, dict):
                raise ValueError(f"Request {idx} must be a dictionary/object")
        return v


class FormsDeleteInput(FormIdInput):
    """Input model for deleting a Google Form."""

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class FormsGetResponsesInput(FormIdInput):
    """Input model for getting form responses."""

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


# ============================================================================
# Tool Implementations
# ============================================================================

@mcp.tool(
    name="forms_create",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def forms_create(params: FormsCreateInput) -> str:
    """Create a new Google Form.

    Creates a blank Google Form with the specified title in the user's Google Drive.
    The form can be edited and configured using the Google Forms interface or API.

    Use this when you need to:
    - Create a new survey or questionnaire
    - Build registration forms for events
    - Generate quizzes or assessments
    - Collect structured data from users

    Args:
        params (FormsCreateInput): Validated parameters with:
            - title: Form title
            - document_title: Optional document title (defaults to form title)
            - response_format: Output format (markdown/json)

    Returns:
        str: Form ID and web URL for editing the created form

    Examples:
        - Create survey: title='Customer Satisfaction Survey 2025'
        - Create registration: title='Annual Conference Registration'
        - Create quiz: title='Python Programming Quiz - Chapter 1'
    """
    try:
        result = await forms_service.create_form(
            title=params.title,
            document_title=params.document_title
        )

        form_id = result.get('formId')
        return create_success_response(
            f"Created form '{result['info']['title']}'",
            data={
                "form_id": form_id,
                "title": result['info']['title'],
                "edit_url": f"https://docs.google.com/forms/d/{form_id}/edit",
                "response_url": f"https://docs.google.com/forms/d/{form_id}/viewform"
            },
            response_format=params.response_format
        )

    except Exception as e:
        logger.error(f"forms_create error: {str(e)}")
        return format_error(e, "creating form")


@mcp.tool(
    name="forms_read",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def forms_read(params: FormsReadInput) -> str:
    """Read structure and content from a Google Form.

    Retrieves form metadata including title and all form items (questions).
    This provides the form structure but does not include response data.

    Use this when you need to:
    - Review form structure and questions
    - Analyze form configuration
    - Understand form layout for integration

    Args:
        params (FormsReadInput): Validated parameters with:
            - form_id: Google Forms form ID
            - response_format: Output format (markdown/json)

    Returns:
        str: Form title, item count, and details of all form items

    Examples:
        - Read survey structure: form_id='1A2B3C4D5E6F'
        - Analyze quiz questions: form_id='9X8Y7Z6W5V4U'

    Note:
        - Returns form structure, not response data
        - Use forms_get_responses to retrieve submitted responses
        - Large forms may be truncated if exceeding 25,000 characters
    """
    try:
        result = await forms_service.read_form(form_id=params.form_id)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2)

        # Markdown format
        response = f"# Form: {result.get('title', 'Untitled')}\\n\\n"
        response += f"**Form ID**: `{result.get('form_id')}`\\n"
        response += f"**Total Items**: {result.get('item_count', 0)}\\n\\n"

        # Add items
        items = result.get('items', [])
        if items:
            response += "## Form Items\\n\\n"
            for i, item in enumerate(items, 1):
                response += f"{i}. **{item.get('title', 'Untitled Item')}** "
                response += f"(Type: {item.get('question_type', 'unknown')})\\n"
        else:
            response += "## Form Items\\n\\n_No items found in form._\\n"

        # Check character limit
        if len(response) > CHARACTER_LIMIT:
            truncated = response[:CHARACTER_LIMIT - 200]
            truncated += "\\n\\n⚠️ **Content Truncated**: Form content exceeds character limit (25,000 chars)."
            truncated += "\\n\\n**Tip**: Consider reading specific sections or reducing form complexity."
            return truncated

        return response

    except Exception as e:
        logger.error(f"forms_read error: {str(e)}")
        return format_error(e, "reading form")


@mcp.tool(
    name="forms_update",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def forms_update(params: FormsUpdateInput) -> str:
    """Update form structure and questions using batch requests.

    Updates the form using Google Forms API batch update requests. This allows
    adding questions, modifying existing items, and configuring form settings.

    Use this when you need to:
    - Add new questions to a form
    - Modify existing form items
    - Update form configuration
    - Programmatically build forms

    Args:
        params (FormsUpdateInput): Validated parameters with:
            - form_id: Google Forms form ID
            - requests: Array of batch update requests
            - response_format: Output format (markdown/json)

    Returns:
        str: Success confirmation with form ID and edit URL

    Examples:
        - Add question: requests=[{"createItem": {"item": {...}, "location": {"index": 0}}}]
        - Update settings: requests=[{"updateSettings": {"settings": {...}}}]

    Note:
        - Requests must follow Google Forms API batchUpdate format
        - Multiple operations can be batched in single update
        - See Google Forms API documentation for request formats
    """
    try:
        await forms_service.update_form(
            form_id=params.form_id,
            requests=params.requests
        )

        return create_success_response(
            f"Updated form successfully",
            data={
                "form_id": params.form_id,
                "requests_processed": len(params.requests),
                "edit_url": f"https://docs.google.com/forms/d/{params.form_id}/edit"
            },
            response_format=params.response_format
        )

    except Exception as e:
        logger.error(f"forms_update error: {str(e)}")
        return format_error(e, "updating form")


@mcp.tool(
    name="forms_delete",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def forms_delete(params: FormsDeleteInput) -> str:
    """Delete a Google Form.

    ⚠️ WARNING: This operation moves the form to trash via Google Drive API.
    The form can be restored from trash within 30 days, after which it is
    permanently deleted. All associated responses are also affected.

    Use this when you need to:
    - Remove obsolete or test forms
    - Clean up form inventory
    - Manage form lifecycle programmatically

    Args:
        params (FormsDeleteInput): Validated parameters with:
            - form_id: Google Forms form ID
            - response_format: Output format (markdown/json)

    Returns:
        str: Confirmation message with form ID

    Examples:
        - Delete test form: form_id='1A2B3C4D5E6F'
        - Remove outdated survey: form_id='9X8Y7Z6W5V4U'

    Warning:
        - Form is moved to trash, not immediately deleted
        - Can be restored from Google Drive trash within 30 days
        - After 30 days, deletion is permanent
        - All form responses are affected
    """
    try:
        await forms_service.delete_form(form_id=params.form_id)

        return create_success_response(
            f"Deleted form with ID: {params.form_id}",
            data={
                "form_id": params.form_id,
                "note": "Form moved to trash. Can be restored from Google Drive trash within 30 days."
            },
            response_format=params.response_format
        )

    except Exception as e:
        logger.error(f"forms_delete error: {str(e)}")
        return format_error(e, "deleting form")


@mcp.tool(
    name="forms_get_responses",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def forms_get_responses(params: FormsGetResponsesInput) -> str:
    """Get responses submitted to a Google Form.

    Retrieves all responses that have been submitted to the form. This includes
    response metadata and answer data for analysis.

    Use this when you need to:
    - Analyze survey results
    - Process form submissions
    - Generate reports from collected data
    - Export response data for analysis

    Args:
        params (FormsGetResponsesInput): Validated parameters with:
            - form_id: Google Forms form ID
            - response_format: Output format (markdown/json)

    Returns:
        str: Response count and response data

    Examples:
        - Get survey responses: form_id='1A2B3C4D5E6F'
        - Analyze quiz submissions: form_id='9X8Y7Z6W5V4U'

    Note:
        - Returns all submitted responses
        - Response data includes timestamps and answers
        - Large response sets may be truncated if exceeding 25,000 characters
        - Cached for 60 seconds for performance
    """
    try:
        result = await forms_service.get_responses(form_id=params.form_id)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2)

        # Markdown format
        response = f"# Form Responses\\n\\n"
        response += f"**Form ID**: `{result.get('form_id')}`\\n"
        response += f"**Total Responses**: {result.get('response_count', 0)}\\n\\n"

        if result.get('response_count', 0) > 0:
            response += "## Response Data\\n\\n"
            response += "_Response data retrieved successfully. Use JSON format for detailed analysis._\\n"
        else:
            response += "## Response Data\\n\\n_No responses submitted yet._\\n"

        # Check character limit
        if len(response) > CHARACTER_LIMIT:
            truncated = response[:CHARACTER_LIMIT - 200]
            truncated += "\\n\\n⚠️ **Content Truncated**: Response data exceeds character limit (25,000 chars)."
            truncated += "\\n\\n**Tip**: Use JSON format or process responses in batches."
            return truncated

        return response

    except Exception as e:
        logger.error(f"forms_get_responses error: {str(e)}")
        return format_error(e, "getting form responses")
