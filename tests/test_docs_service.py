"""Tests for Docs service."""

import pytest
from unittest.mock import Mock, patch
from src.services.docs_service import DocsService


@pytest.mark.asyncio
class TestDocsService:
    """Test Docs service operations."""

    @patch('src.services.docs_service.OAuthHandler')
    async def test_create_document(self, mock_oauth_class, mock_docs_service):
        """Test document creation."""
        mock_oauth_class.return_value.get_service.return_value = mock_docs_service

        service = DocsService()
        result = await service.create_document(title="Test Document")

        assert result['documentId'] == 'doc1'
        assert result['title'] == 'Test Document'
        mock_docs_service.documents().create.assert_called_once()

    @patch('src.services.docs_service.OAuthHandler')
    async def test_read_document(self, mock_oauth_class, mock_docs_service):
        """Test document reading."""
        mock_oauth_class.return_value.get_service.return_value = mock_docs_service

        service = DocsService()
        result = await service.read_document(document_id="doc1")

        assert result['document_id'] == 'doc1'
        assert result['title'] == 'Test Document'
        assert 'content' in result
        mock_docs_service.documents().get.assert_called_once()

    @patch('src.services.docs_service.OAuthHandler')
    async def test_update_document(self, mock_oauth_class, mock_docs_service):
        """Test document update."""
        mock_oauth_class.return_value.get_service.return_value = mock_docs_service

        service = DocsService()
        await service.update_document(
            document_id="doc1",
            text="New text",
            index=1
        )

        mock_docs_service.documents().batchUpdate.assert_called_once()

    @patch('src.services.docs_service.OAuthHandler')
    async def test_delete_document(self, mock_oauth_class, mock_drive_service):
        """Test document deletion."""
        mock_oauth_class.return_value.get_service.return_value = mock_drive_service
        mock_drive_service.files().delete().execute.return_value = None

        service = DocsService()
        await service.delete_document(document_id="doc1")

        mock_drive_service.files().delete.assert_called_once()

    @patch('src.services.docs_service.OAuthHandler')
    async def test_error_handling(self, mock_oauth_class, mock_docs_service):
        """Test error handling."""
        from src.utils.error_handler import GoogleWorkspaceError

        mock_oauth_class.return_value.get_service.return_value = mock_docs_service
        mock_docs_service.documents().get().execute.side_effect = Exception("API Error")

        service = DocsService()

        with pytest.raises(GoogleWorkspaceError):
            await service.read_document(document_id="invalid")
