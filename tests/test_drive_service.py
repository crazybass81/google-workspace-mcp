"""Tests for Drive service."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.drive_service import DriveService


@pytest.mark.asyncio
class TestDriveService:
    """Test Drive service operations."""

    @patch('src.services.drive_service.OAuthHandler')
    async def test_search_files(self, mock_oauth_class, mock_drive_service):
        """Test file search functionality."""
        mock_oauth_class.return_value.get_service.return_value = mock_drive_service

        service = DriveService()
        results = await service.search_files(query="test")

        assert len(results) == 1
        assert results[0]['name'] == 'test.txt'
        mock_drive_service.files().list.assert_called_once()

    @patch('src.services.drive_service.OAuthHandler')
    async def test_read_file(self, mock_oauth_class, mock_drive_service):
        """Test file reading."""
        mock_oauth_class.return_value.get_service.return_value = mock_drive_service

        service = DriveService()
        content = await service.read_file(file_id="file1")

        assert 'content' in content
        assert content['content'] == 'test content'
        mock_drive_service.files().get_media.assert_called_once()

    @patch('src.services.drive_service.OAuthHandler')
    async def test_create_file(self, mock_oauth_class, mock_drive_service):
        """Test file creation."""
        mock_oauth_class.return_value.get_service.return_value = mock_drive_service

        service = DriveService()
        result = await service.create_file(
            name="new.txt",
            content="test content"
        )

        assert result['id'] == 'new_file'
        assert result['name'] == 'new.txt'
        mock_drive_service.files().create.assert_called_once()

    @patch('src.services.drive_service.OAuthHandler')
    async def test_update_file(self, mock_oauth_class, mock_drive_service):
        """Test file update."""
        mock_oauth_class.return_value.get_service.return_value = mock_drive_service

        service = DriveService()
        result = await service.update_file(
            file_id="file1",
            content="updated content"
        )

        assert result['id'] == 'file1'
        mock_drive_service.files().update.assert_called_once()

    @patch('src.services.drive_service.OAuthHandler')
    async def test_delete_file(self, mock_oauth_class, mock_drive_service):
        """Test file deletion."""
        mock_oauth_class.return_value.get_service.return_value = mock_drive_service
        mock_drive_service.files().delete().execute.return_value = None

        service = DriveService()
        await service.delete_file(file_id="file1")

        mock_drive_service.files().delete.assert_called_once()

    @patch('src.services.drive_service.OAuthHandler')
    async def test_list_shared_drives(self, mock_oauth_class, mock_drive_service):
        """Test shared drives listing."""
        mock_oauth_class.return_value.get_service.return_value = mock_drive_service

        service = DriveService()
        drives = await service.list_shared_drives()

        assert len(drives) == 1
        assert drives[0]['name'] == 'Shared Drive'
        mock_drive_service.drives().list.assert_called_once()

    @patch('src.services.drive_service.OAuthHandler')
    async def test_search_with_filters(self, mock_oauth_class, mock_drive_service):
        """Test file search with filters."""
        mock_oauth_class.return_value.get_service.return_value = mock_drive_service

        service = DriveService()
        results = await service.search_files(
            query="test",
            folder_id="folder1",
            file_type="text/plain",
            max_results=10
        )

        assert len(results) == 1
        call_args = mock_drive_service.files().list.call_args
        assert 'q' in call_args[1]

    @patch('src.services.drive_service.OAuthHandler')
    async def test_error_handling(self, mock_oauth_class, mock_drive_service):
        """Test error handling."""
        from src.utils.error_handler import GoogleWorkspaceError

        mock_oauth_class.return_value.get_service.return_value = mock_drive_service
        mock_drive_service.files().get().execute.side_effect = Exception("API Error")

        service = DriveService()

        with pytest.raises(GoogleWorkspaceError):
            await service.read_file(file_id="invalid")
