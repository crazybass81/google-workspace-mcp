"""Tests for Slides tools handlers."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from mcp.types import TextContent
from src.tools.slides_tools import (
    handle_slides_tool,
    SLIDES_TOOLS
)


@pytest.mark.asyncio
class TestSlidesToolsRegistration:
    """Test Slides tools registration and schemas."""

    def test_all_slides_tools_registered(self):
        """Test that all 5 Slides tools are registered."""
        assert len(SLIDES_TOOLS) == 5

        tool_names = [tool.name for tool in SLIDES_TOOLS]
        assert 'slides_create' in tool_names
        assert 'slides_read' in tool_names
        assert 'slides_add_slide' in tool_names
        assert 'slides_update' in tool_names
        assert 'slides_delete' in tool_names

    def test_slides_tools_schemas(self):
        """Test that all Slides tools have valid schemas."""
        for tool in SLIDES_TOOLS:
            assert tool.name is not None
            assert tool.description is not None
            assert tool.inputSchema is not None
            assert 'type' in tool.inputSchema
            assert tool.inputSchema['type'] == 'object'
            assert 'properties' in tool.inputSchema


@pytest.mark.asyncio
class TestSlidesToolHandlers:
    """Test Slides tool handlers with proper mocking."""

    @patch('src.tools.slides_tools.slides_service')
    async def test_create_handler(self, mock_service):
        """Test slides_create tool handler."""
        mock_service.create_presentation = AsyncMock(return_value={
            'presentationId': 'pres1',
            'title': 'Test Presentation'
        })

        result = await handle_slides_tool('slides_create', {'title': 'Test Presentation'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'pres1' in result[0].text
        mock_service.create_presentation.assert_called_once_with(title='Test Presentation')

    @patch('src.tools.slides_tools.slides_service')
    async def test_read_handler(self, mock_service):
        """Test slides_read tool handler."""
        mock_service.read_presentation = AsyncMock(return_value={
            'presentationId': 'pres1',
            'title': 'Test Presentation',
            'slides': [{'objectId': 'slide1'}]
        })

        result = await handle_slides_tool('slides_read', {'presentation_id': 'pres1'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'pres1' in result[0].text
        mock_service.read_presentation.assert_called_once_with(presentation_id='pres1')

    @patch('src.tools.slides_tools.slides_service')
    async def test_add_slide_handler(self, mock_service):
        """Test slides_add_slide tool handler."""
        mock_service.add_slide = AsyncMock(return_value={
            'replies': [{'createSlide': {'objectId': 'new_slide'}}]
        })

        result = await handle_slides_tool('slides_add_slide', {
            'presentation_id': 'pres1',
            'insertion_index': 1
        })

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'new_slide' in result[0].text
        mock_service.add_slide.assert_called_once()

    @patch('src.tools.slides_tools.slides_service')
    async def test_update_handler(self, mock_service):
        """Test slides_update tool handler."""
        mock_service.batch_update = AsyncMock(return_value={
            'replies': [],
            'presentationId': 'pres1'
        })

        result = await handle_slides_tool('slides_update', {
            'presentation_id': 'pres1',
            'requests': [{}]
        })

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'pres1' in result[0].text
        mock_service.batch_update.assert_called_once()

    @patch('src.tools.slides_tools.slides_service')
    async def test_delete_handler(self, mock_service):
        """Test slides_delete tool handler."""
        mock_service.delete_presentation = AsyncMock(return_value={'success': True})

        result = await handle_slides_tool('slides_delete', {'presentation_id': 'pres1'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'successfully' in result[0].text.lower()
        mock_service.delete_presentation.assert_called_once_with(presentation_id='pres1')

    @patch('src.tools.slides_tools.slides_service')
    async def test_error_handling(self, mock_service):
        """Test error handling in Slides tool handlers."""
        from src.utils.error_handler import GoogleWorkspaceError

        mock_service.create_presentation = AsyncMock(
            side_effect=GoogleWorkspaceError("API Error", "Test error")
        )

        result = await handle_slides_tool('slides_create', {'title': 'Test'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'Error' in result[0].text

    async def test_invalid_tool_name(self):
        """Test handling of invalid tool name."""
        result = await handle_slides_tool('invalid_tool', {})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'Unknown' in result[0].text or 'Error' in result[0].text
