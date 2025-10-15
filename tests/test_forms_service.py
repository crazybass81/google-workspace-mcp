"""Tests for Forms service."""

import pytest
from unittest.mock import Mock, patch
from src.services.forms_service import FormsService


@pytest.mark.asyncio
class TestFormsService:
    """Test Forms service operations."""

    @patch('src.services.forms_service.OAuthHandler')
    async def test_create_form(self, mock_oauth_class, mock_forms_service):
        """Test form creation."""
        mock_oauth_class.return_value.get_service.return_value = mock_forms_service

        service = FormsService()
        result = await service.create_form(title="Test Form")

        assert result['formId'] == 'form1'
        assert result['info']['title'] == 'Test Form'
        mock_forms_service.forms().create.assert_called_once()

    @patch('src.services.forms_service.OAuthHandler')
    async def test_read_form(self, mock_oauth_class, mock_forms_service):
        """Test form reading."""
        mock_oauth_class.return_value.get_service.return_value = mock_forms_service

        service = FormsService()
        result = await service.read_form(form_id="form1")

        assert result['form_id'] == 'form1'
        assert result['title'] == 'Test Form'
        assert result['item_count'] == 0
        mock_forms_service.forms().get.assert_called_once()

    @patch('src.services.forms_service.OAuthHandler')
    async def test_update_form(self, mock_oauth_class, mock_forms_service):
        """Test form update."""
        mock_oauth_class.return_value.get_service.return_value = mock_forms_service

        service = FormsService()
        requests = [
            {
                'createItem': {
                    'item': {
                        'title': 'Question 1',
                        'questionItem': {
                            'question': {
                                'required': True,
                                'textQuestion': {}
                            }
                        }
                    },
                    'location': {'index': 0}
                }
            }
        ]
        await service.update_form(form_id="form1", requests=requests)

        mock_forms_service.forms().batchUpdate.assert_called_once()

    @patch('src.services.forms_service.OAuthHandler')
    async def test_delete_form(self, mock_oauth_class, mock_drive_service):
        """Test form deletion."""
        mock_oauth_class.return_value.get_service.return_value = mock_drive_service
        mock_drive_service.files().delete().execute.return_value = None

        service = FormsService()
        await service.delete_form(form_id="form1")

        mock_drive_service.files().delete.assert_called_once()

    @patch('src.services.forms_service.OAuthHandler')
    async def test_get_responses(self, mock_oauth_class, mock_forms_service):
        """Test getting form responses."""
        mock_oauth_class.return_value.get_service.return_value = mock_forms_service

        service = FormsService()
        result = await service.get_responses(form_id="form1")

        assert result['form_id'] == 'form1'
        assert result['response_count'] == 0
        mock_forms_service.forms().responses().list.assert_called_once()

    @patch('src.services.forms_service.OAuthHandler')
    async def test_error_handling(self, mock_oauth_class, mock_forms_service):
        """Test error handling."""
        from src.utils.error_handler import GoogleWorkspaceError

        mock_oauth_class.return_value.get_service.return_value = mock_forms_service
        mock_forms_service.forms().get().execute.side_effect = Exception("API Error")

        service = FormsService()

        with pytest.raises(GoogleWorkspaceError):
            await service.read_form(form_id="invalid")
