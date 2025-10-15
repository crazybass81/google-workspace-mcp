"""Tests for Docs tools handlers."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from mcp.types import TextContent
from src.tools.docs_tools import (
    handle_docs_tool,
    DOCS_TOOLS
)


@pytest.mark.asyncio
class TestDocsToolsRegistration:
    """Test Docs tools registration and schemas."""

    def test_all_docs_tools_registered(self):
        """Test that all 4 Docs tools are registered."""
        assert len(DOCS_TOOLS) == 4

        tool_names = [tool.name for tool in DOCS_TOOLS]
        assert 'docs_create' in tool_names
        assert 'docs_read' in tool_names
        assert 'docs_update' in tool_names
        assert 'docs_delete' in tool_names

    def test_docs_tools_schemas(self):
        """Test that all Docs tools have valid schemas."""
        for tool in DOCS_TOOLS:
            assert tool.name is not None
            assert tool.description is not None
            assert tool.inputSchema is not None
            assert 'type' in tool.inputSchema
            assert tool.inputSchema['type'] == 'object'
            assert 'properties' in tool.inputSchema


@pytest.mark.asyncio
class TestDocsToolHandlers:
    """Test Docs tool handlers with proper mocking."""

    @patch('src.tools.docs_tools.docs_service')
    async def test_create_handler(self, mock_service):
        """Test docs_create tool handler."""
        mock_service.create_document = AsyncMock(return_value={
            'documentId': 'doc1',
            'title': 'Test Doc'
        })

        result = await handle_docs_tool('docs_create', {'title': 'Test Doc'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'doc1' in result[0].text
        assert 'Test Doc' in result[0].text
        mock_service.create_document.assert_called_once_with(title='Test Doc')

    @patch('src.tools.docs_tools.docs_service')
    async def test_read_handler(self, mock_service):
        """Test docs_read tool handler."""
        mock_service.read_document = AsyncMock(return_value={
            'documentId': 'doc1',
            'document_id': 'doc1',
            'title': 'Test Doc',
            'content': 'Test content'
        })

        result = await handle_docs_tool('docs_read', {'document_id': 'doc1'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'doc1' in result[0].text
        assert 'Test content' in result[0].text
        mock_service.read_document.assert_called_once_with(document_id='doc1')

    @patch('src.tools.docs_tools.docs_service')
    async def test_update_handler(self, mock_service):
        """Test docs_update tool handler."""
        mock_service.update_document = AsyncMock(return_value={
            'documentId': 'doc1'
        })

        result = await handle_docs_tool('docs_update', {
            'document_id': 'doc1',
            'text': 'New content'
        })

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'doc1' in result[0].text
        mock_service.update_document.assert_called_once()

    @patch('src.tools.docs_tools.docs_service')
    async def test_delete_handler(self, mock_service):
        """Test docs_delete tool handler."""
        mock_service.delete_document = AsyncMock(return_value={'success': True})

        result = await handle_docs_tool('docs_delete', {'document_id': 'doc1'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'successfully' in result[0].text.lower()
        mock_service.delete_document.assert_called_once_with('doc1')

    @patch('src.tools.docs_tools.docs_service')
    async def test_error_handling(self, mock_service):
        """Test error handling in Docs tool handlers."""
        from src.utils.error_handler import GoogleWorkspaceError

        mock_service.create_document = AsyncMock(
            side_effect=GoogleWorkspaceError("API Error", "Test error")
        )

        result = await handle_docs_tool('docs_create', {'title': 'Test'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'Error' in result[0].text
        assert 'API Error' in result[0].text

    async def test_invalid_tool_name(self):
        """Test handling of invalid tool name."""
        result = await handle_docs_tool('invalid_tool', {})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'Unknown' in result[0].text or 'Error' in result[0].text
