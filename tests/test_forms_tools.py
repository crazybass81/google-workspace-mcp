"""Tests for Forms tools handlers."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from mcp.types import TextContent
from src.tools.forms_tools import (
    handle_forms_tool,
    FORMS_TOOLS
)


@pytest.mark.asyncio
class TestFormsToolsRegistration:
    """Test Forms tools registration and schemas."""

    def test_all_forms_tools_registered(self):
        """Test that all 5 Forms tools are registered."""
        assert len(FORMS_TOOLS) == 5

        tool_names = [tool.name for tool in FORMS_TOOLS]
        assert 'forms_create' in tool_names
        assert 'forms_read' in tool_names
        assert 'forms_update' in tool_names
        assert 'forms_delete' in tool_names
        assert 'forms_get_responses' in tool_names

    def test_forms_tools_schemas(self):
        """Test that all Forms tools have valid schemas."""
        for tool in FORMS_TOOLS:
            assert tool.name is not None
            assert tool.description is not None
            assert tool.inputSchema is not None
            assert 'type' in tool.inputSchema
            assert tool.inputSchema['type'] == 'object'
            assert 'properties' in tool.inputSchema


@pytest.mark.asyncio
class TestFormsToolHandlers:
    """Test Forms tool handlers with proper mocking."""

    @patch('src.tools.forms_tools.forms_service')
    async def test_create_handler(self, mock_service):
        """Test forms_create tool handler."""
        mock_service.create_form = AsyncMock(return_value={
            'formId': 'form1',
            'info': {'title': 'Test Form'}
        })

        result = await handle_forms_tool('forms_create', {'title': 'Test Form'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'form1' in result[0].text
        mock_service.create_form.assert_called_once_with(title='Test Form')

    @patch('src.tools.forms_tools.forms_service')
    async def test_read_handler(self, mock_service):
        """Test forms_read tool handler."""
        mock_service.read_form = AsyncMock(return_value={
            'formId': 'form1',
            'info': {'title': 'Test Form'},
            'items': []
        })

        result = await handle_forms_tool('forms_read', {'form_id': 'form1'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'form1' in result[0].text
        mock_service.read_form.assert_called_once_with(form_id='form1')

    @patch('src.tools.forms_tools.forms_service')
    async def test_update_handler(self, mock_service):
        """Test forms_update tool handler."""
        mock_service.update_form = AsyncMock(return_value={
            'formId': 'form1',
            'replies': []
        })

        result = await handle_forms_tool('forms_update', {
            'form_id': 'form1',
            'requests': [{}]
        })

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'form1' in result[0].text
        mock_service.update_form.assert_called_once()

    @patch('src.tools.forms_tools.forms_service')
    async def test_delete_handler(self, mock_service):
        """Test forms_delete tool handler."""
        mock_service.delete_form = AsyncMock(return_value={'success': True})

        result = await handle_forms_tool('forms_delete', {'form_id': 'form1'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'successfully' in result[0].text.lower()
        mock_service.delete_form.assert_called_once_with(form_id='form1')

    @patch('src.tools.forms_tools.forms_service')
    async def test_get_responses_handler(self, mock_service):
        """Test forms_get_responses tool handler."""
        mock_service.get_responses = AsyncMock(return_value={
            'responses': [{'responseId': 'resp1'}]
        })

        result = await handle_forms_tool('forms_get_responses', {'form_id': 'form1'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'resp1' in result[0].text
        mock_service.get_responses.assert_called_once_with(form_id='form1')

    @patch('src.tools.forms_tools.forms_service')
    async def test_error_handling(self, mock_service):
        """Test error handling in Forms tool handlers."""
        from src.utils.error_handler import GoogleWorkspaceError

        mock_service.create_form = AsyncMock(
            side_effect=GoogleWorkspaceError("API Error", "Test error")
        )

        result = await handle_forms_tool('forms_create', {'title': 'Test'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'Error' in result[0].text

    async def test_invalid_tool_name(self):
        """Test handling of invalid tool name."""
        result = await handle_forms_tool('invalid_tool', {})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'Unknown' in result[0].text or 'Error' in result[0].text
