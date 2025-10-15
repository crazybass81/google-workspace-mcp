"""Tests for Drive tools handlers."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from mcp.types import TextContent
from src.tools.drive_tools import handle_drive_tool, DRIVE_TOOLS


@pytest.mark.asyncio
class TestDriveToolsRegistration:
    """Test Drive tools registration and schemas."""

    def test_all_drive_tools_registered(self):
        """Test that all 8 Drive tools are registered."""
        assert len(DRIVE_TOOLS) == 8

        tool_names = [tool.name for tool in DRIVE_TOOLS]
        assert 'drive_search_files' in tool_names
        assert 'drive_read_file' in tool_names
        assert 'drive_create_file' in tool_names
        assert 'drive_update_file' in tool_names
        assert 'drive_upload_file' in tool_names
        assert 'drive_download_file' in tool_names
        assert 'drive_delete_file' in tool_names
        assert 'drive_list_shared_drives' in tool_names

    def test_drive_tools_schemas(self):
        """Test that all Drive tools have valid schemas."""
        for tool in DRIVE_TOOLS:
            assert tool.name is not None
            assert tool.description is not None
            assert tool.inputSchema is not None
            assert 'type' in tool.inputSchema
            assert tool.inputSchema['type'] == 'object'
            assert 'properties' in tool.inputSchema


@pytest.mark.asyncio
class TestDriveToolHandlers:
    """Test Drive tool handlers with proper mocking."""

    @patch('src.tools.drive_tools.drive_service')
    async def test_search_files_handler(self, mock_service):
        """Test drive_search_files tool handler."""
        # Setup mock
        mock_service.search_files = AsyncMock(return_value=[
            {'id': 'file1', 'name': 'test.txt', 'mimeType': 'text/plain'}
        ])

        # Execute
        result = await handle_drive_tool('drive_search_files', {'query': 'test'})

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'file1' in result[0].text
        assert 'test.txt' in result[0].text
        mock_service.search_files.assert_called_once_with(query='test')

    @patch('src.tools.drive_tools.drive_service')
    async def test_read_file_handler(self, mock_service):
        """Test drive_read_file tool handler."""
        # Setup mock
        mock_service.read_file = AsyncMock(return_value={
            'metadata': {
                'name': 'test.txt',
                'mimeType': 'text/plain',
                'modifiedTime': '2024-01-01T00:00:00Z'
            },
            'content': 'test content'
        })

        # Execute
        result = await handle_drive_tool('drive_read_file', {'file_id': 'file1'})

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'test content' in result[0].text
        mock_service.read_file.assert_called_once_with(file_id='file1')

    @patch('src.tools.drive_tools.drive_service')
    async def test_create_file_handler(self, mock_service):
        """Test drive_create_file tool handler."""
        # Setup mock
        mock_service.create_file = AsyncMock(return_value={
            'id': 'new_file',
            'name': 'new.txt'
        })

        # Execute
        result = await handle_drive_tool('drive_create_file', {
            'name': 'new.txt',
            'content': 'new content'
        })

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'new_file' in result[0].text
        mock_service.create_file.assert_called_once()

    @patch('src.tools.drive_tools.drive_service')
    async def test_update_file_handler(self, mock_service):
        """Test drive_update_file tool handler."""
        # Setup mock
        mock_service.update_file = AsyncMock(return_value={
            'id': 'file1',
            'name': 'updated.txt',
            'modifiedTime': '2024-01-01T00:00:00Z'
        })

        # Execute
        result = await handle_drive_tool('drive_update_file', {
            'file_id': 'file1',
            'content': 'updated content'
        })

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'file1' in result[0].text
        mock_service.update_file.assert_called_once()

    @patch('src.tools.drive_tools.drive_service')
    async def test_upload_file_handler(self, mock_service):
        """Test drive_upload_file tool handler."""
        # Setup mock
        mock_service.upload_file = AsyncMock(return_value={
            'id': 'uploaded_file',
            'name': 'uploaded.pdf'
        })

        # Execute
        result = await handle_drive_tool('drive_upload_file', {
            'local_path': '/path/to/file.pdf'
        })

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'uploaded_file' in result[0].text
        mock_service.upload_file.assert_called_once()

    @patch('src.tools.drive_tools.drive_service')
    async def test_download_file_handler(self, mock_service):
        """Test drive_download_file tool handler."""
        # Setup mock
        mock_service.download_file = AsyncMock(return_value={'size': 1024})

        # Execute
        result = await handle_drive_tool('drive_download_file', {
            'file_id': 'file1',
            'local_path': '/tmp/downloaded.pdf'
        })

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert '/tmp/downloaded.pdf' in result[0].text
        mock_service.download_file.assert_called_once()

    @patch('src.tools.drive_tools.drive_service')
    async def test_delete_file_handler(self, mock_service):
        """Test drive_delete_file tool handler."""
        # Setup mock
        mock_service.delete_file = AsyncMock(return_value=None)

        # Execute
        result = await handle_drive_tool('drive_delete_file', {'file_id': 'file1'})

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'successfully' in result[0].text.lower()
        mock_service.delete_file.assert_called_once_with('file1')

    @patch('src.tools.drive_tools.drive_service')
    async def test_list_shared_drives_handler(self, mock_service):
        """Test drive_list_shared_drives tool handler."""
        # Setup mock
        mock_service.list_shared_drives = AsyncMock(return_value=[
            {'id': 'drive1', 'name': 'Team Drive 1'},
            {'id': 'drive2', 'name': 'Team Drive 2'}
        ])

        # Execute
        result = await handle_drive_tool('drive_list_shared_drives', {})

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'drive1' in result[0].text
        assert 'Team Drive 1' in result[0].text
        mock_service.list_shared_drives.assert_called_once()

    @patch('src.tools.drive_tools.drive_service')
    async def test_error_handling(self, mock_service):
        """Test error handling in Drive tool handlers."""
        from src.utils.error_handler import GoogleWorkspaceError

        # Setup mock to raise error
        mock_service.search_files = AsyncMock(side_effect=GoogleWorkspaceError(
            "API Error",
            "Test error"
        ))

        # Execute
        result = await handle_drive_tool('drive_search_files', {'query': 'test'})

        # Verify error handling
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'Error' in result[0].text
        assert 'API Error' in result[0].text

    async def test_invalid_tool_name(self):
        """Test handling of invalid tool name."""
        result = await handle_drive_tool('invalid_tool', {})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'Unknown' in result[0].text or 'Error' in result[0].text
