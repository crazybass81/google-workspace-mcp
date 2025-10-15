"""Tests for Gmail service."""

import pytest
from unittest.mock import Mock, patch
from src.services.gmail_service import GmailService


@pytest.mark.asyncio
class TestGmailService:
    """Test Gmail service operations."""

    @patch('src.services.gmail_service.OAuthHandler')
    async def test_search_messages(self, mock_oauth_class, mock_gmail_service):
        """Test message search."""
        mock_oauth_class.return_value.get_service.return_value = mock_gmail_service

        service = GmailService()
        results = await service.search_messages(query="test")

        assert len(results) == 1
        assert results[0]['id'] == 'msg1'
        mock_gmail_service.users().messages().list.assert_called_once()

    @patch('src.services.gmail_service.OAuthHandler')
    async def test_read_message(self, mock_oauth_class, mock_gmail_service):
        """Test message reading."""
        mock_oauth_class.return_value.get_service.return_value = mock_gmail_service

        service = GmailService()
        result = await service.read_message(message_id="msg1")

        assert result['message_id'] == 'msg1'
        assert result['headers']['From'] == 'test@example.com'
        assert result['headers']['Subject'] == 'Test Subject'
        assert 'body' in result
        mock_gmail_service.users().messages().get.assert_called_once()

    @patch('src.services.gmail_service.OAuthHandler')
    async def test_send_message(self, mock_oauth_class, mock_gmail_service):
        """Test sending message."""
        mock_oauth_class.return_value.get_service.return_value = mock_gmail_service

        service = GmailService()
        result = await service.send_message(
            to="recipient@example.com",
            subject="Test Subject",
            body="Test body"
        )

        assert result['id'] == 'sent1'
        mock_gmail_service.users().messages().send.assert_called_once()

    @patch('src.services.gmail_service.OAuthHandler')
    async def test_reply_message(self, mock_oauth_class, mock_gmail_service):
        """Test replying to message."""
        mock_oauth_class.return_value.get_service.return_value = mock_gmail_service

        service = GmailService()
        result = await service.reply_message(
            message_id="msg1",
            body="Reply body"
        )

        assert result['id'] == 'sent1'
        mock_gmail_service.users().messages().send.assert_called()

    @patch('src.services.gmail_service.OAuthHandler')
    async def test_delete_message(self, mock_oauth_class, mock_gmail_service):
        """Test message deletion."""
        mock_oauth_class.return_value.get_service.return_value = mock_gmail_service
        mock_gmail_service.users().messages().trash().execute.return_value = {'id': 'msg1'}

        service = GmailService()
        await service.delete_message(message_id="msg1")

        mock_gmail_service.users().messages().trash.assert_called_once()

    @patch('src.services.gmail_service.OAuthHandler')
    async def test_list_labels(self, mock_oauth_class, mock_gmail_service):
        """Test listing labels."""
        mock_oauth_class.return_value.get_service.return_value = mock_gmail_service

        service = GmailService()
        labels = await service.list_labels()

        assert len(labels) == 2
        assert labels[0]['name'] == 'INBOX'
        mock_gmail_service.users().labels().list.assert_called_once()

    @patch('src.services.gmail_service.OAuthHandler')
    async def test_modify_labels(self, mock_oauth_class, mock_gmail_service):
        """Test modifying message labels."""
        mock_oauth_class.return_value.get_service.return_value = mock_gmail_service

        service = GmailService()
        result = await service.modify_labels(
            message_id="msg1",
            add_labels=['UNREAD'],
            remove_labels=['INBOX']
        )

        assert 'UNREAD' in result['labelIds']
        mock_gmail_service.users().messages().modify.assert_called_once()

    @patch('src.services.gmail_service.OAuthHandler')
    async def test_search_with_filters(self, mock_oauth_class, mock_gmail_service):
        """Test message search with filters."""
        mock_oauth_class.return_value.get_service.return_value = mock_gmail_service

        service = GmailService()
        results = await service.search_messages(
            query="test",
            max_results=50,
            label_ids=['INBOX', 'UNREAD']
        )

        assert len(results) == 1
        call_args = mock_gmail_service.users().messages().list.call_args
        assert 'q' in call_args[1]
        assert 'labelIds' in call_args[1]

    @patch('src.services.gmail_service.OAuthHandler')
    async def test_error_handling(self, mock_oauth_class, mock_gmail_service):
        """Test error handling."""
        from src.utils.error_handler import GoogleWorkspaceError

        mock_oauth_class.return_value.get_service.return_value = mock_gmail_service
        mock_gmail_service.users().messages().get().execute.side_effect = Exception("API Error")

        service = GmailService()

        with pytest.raises(GoogleWorkspaceError):
            await service.read_message(message_id="invalid")
