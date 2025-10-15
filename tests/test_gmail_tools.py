"""Tests for Gmail tools handlers."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from mcp.types import TextContent
from src.tools.gmail_tools import (
    handle_gmail_tool,
    GMAIL_TOOLS
)


@pytest.mark.asyncio
class TestGmailToolsRegistration:
    """Test Gmail tools registration and schemas."""

    def test_all_gmail_tools_registered(self):
        """Test that all 7 Gmail tools are registered."""
        assert len(GMAIL_TOOLS) == 7

        tool_names = [tool.name for tool in GMAIL_TOOLS]
        assert 'gmail_search_messages' in tool_names
        assert 'gmail_read_message' in tool_names
        assert 'gmail_send_message' in tool_names
        assert 'gmail_reply_message' in tool_names
        assert 'gmail_delete_message' in tool_names
        assert 'gmail_list_labels' in tool_names
        assert 'gmail_modify_labels' in tool_names

    def test_gmail_tools_schemas(self):
        """Test that all Gmail tools have valid schemas."""
        for tool in GMAIL_TOOLS:
            assert tool.name is not None
            assert tool.description is not None
            assert tool.inputSchema is not None
            assert 'type' in tool.inputSchema
            assert tool.inputSchema['type'] == 'object'
            assert 'properties' in tool.inputSchema


@pytest.mark.asyncio
class TestGmailToolHandlers:
    """Test Gmail tool handlers with proper mocking."""

    @patch('src.tools.gmail_tools.gmail_service')
    async def test_search_messages_handler(self, mock_service):
        """Test gmail_search_messages tool handler."""
        mock_service.search_messages = AsyncMock(return_value=[
            {'id': 'msg1', 'threadId': 'thread1', 'snippet': 'Test'}
        ])

        result = await handle_gmail_tool('gmail_search_messages', {'query': 'test'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'msg1' in result[0].text
        mock_service.search_messages.assert_called_once()

    @patch('src.tools.gmail_tools.gmail_service')
    async def test_read_message_handler(self, mock_service):
        """Test gmail_read_message tool handler."""
        mock_service.read_message = AsyncMock(return_value={
            'id': 'msg1',
            'payload': {'headers': []},
            'snippet': 'Test message'
        })

        result = await handle_gmail_tool('gmail_read_message', {'message_id': 'msg1'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'msg1' in result[0].text
        mock_service.read_message.assert_called_once_with(message_id='msg1')

    @patch('src.tools.gmail_tools.gmail_service')
    async def test_send_message_handler(self, mock_service):
        """Test gmail_send_message tool handler."""
        mock_service.send_message = AsyncMock(return_value={
            'id': 'msg1',
            'threadId': 'thread1'
        })

        result = await handle_gmail_tool('gmail_send_message', {
            'to': 'test@example.com',
            'subject': 'Test',
            'body': 'Test message'
        })

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'msg1' in result[0].text
        mock_service.send_message.assert_called_once()

    @patch('src.tools.gmail_tools.gmail_service')
    async def test_reply_message_handler(self, mock_service):
        """Test gmail_reply_message tool handler."""
        mock_service.reply_message = AsyncMock(return_value={
            'id': 'msg2',
            'threadId': 'thread1'
        })

        result = await handle_gmail_tool('gmail_reply_message', {
            'message_id': 'msg1',
            'body': 'Reply text'
        })

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'msg2' in result[0].text
        mock_service.reply_message.assert_called_once()

    @patch('src.tools.gmail_tools.gmail_service')
    async def test_delete_message_handler(self, mock_service):
        """Test gmail_delete_message tool handler."""
        mock_service.delete_message = AsyncMock(return_value={'success': True})

        result = await handle_gmail_tool('gmail_delete_message', {'message_id': 'msg1'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'successfully' in result[0].text.lower()
        mock_service.delete_message.assert_called_once_with(message_id='msg1')

    @patch('src.tools.gmail_tools.gmail_service')
    async def test_list_labels_handler(self, mock_service):
        """Test gmail_list_labels tool handler."""
        mock_service.list_labels = AsyncMock(return_value=[
            {'id': 'label1', 'name': 'Important'}
        ])

        result = await handle_gmail_tool('gmail_list_labels', {})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'label1' in result[0].text
        mock_service.list_labels.assert_called_once()

    @patch('src.tools.gmail_tools.gmail_service')
    async def test_modify_labels_handler(self, mock_service):
        """Test gmail_modify_labels tool handler."""
        mock_service.modify_labels = AsyncMock(return_value={
            'id': 'msg1',
            'labelIds': ['INBOX', 'label1']
        })

        result = await handle_gmail_tool('gmail_modify_labels', {
            'message_id': 'msg1',
            'add_labels': ['label1']
        })

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'msg1' in result[0].text
        mock_service.modify_labels.assert_called_once()

    @patch('src.tools.gmail_tools.gmail_service')
    async def test_error_handling(self, mock_service):
        """Test error handling in Gmail tool handlers."""
        from src.utils.error_handler import GoogleWorkspaceError

        mock_service.search_messages = AsyncMock(
            side_effect=GoogleWorkspaceError("API Error", "Test error")
        )

        result = await handle_gmail_tool('gmail_search_messages', {'query': 'test'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'Error' in result[0].text

    async def test_invalid_tool_name(self):
        """Test handling of invalid tool name."""
        result = await handle_gmail_tool('invalid_tool', {})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'Unknown' in result[0].text or 'Error' in result[0].text
