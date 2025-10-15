"""Tests for Slides service."""

import pytest
from unittest.mock import Mock, patch
from src.services.slides_service import SlidesService


@pytest.mark.asyncio
class TestSlidesService:
    """Test Slides service operations."""

    @patch('src.services.slides_service.OAuthHandler')
    async def test_create_presentation(self, mock_oauth_class, mock_slides_service):
        """Test presentation creation."""
        mock_oauth_class.return_value.get_service.return_value = mock_slides_service

        service = SlidesService()
        result = await service.create_presentation(title="Test Presentation")

        assert result['presentationId'] == 'pres1'
        assert result['title'] == 'Test Presentation'
        mock_slides_service.presentations().create.assert_called_once()

    @patch('src.services.slides_service.OAuthHandler')
    async def test_read_presentation(self, mock_oauth_class, mock_slides_service):
        """Test presentation reading."""
        mock_oauth_class.return_value.get_service.return_value = mock_slides_service

        service = SlidesService()
        result = await service.read_presentation(presentation_id="pres1")

        assert result['presentation_id'] == 'pres1'
        assert result['title'] == 'Test Presentation'
        assert result['slide_count'] == 1
        mock_slides_service.presentations().get.assert_called_once()

    @patch('src.services.slides_service.OAuthHandler')
    async def test_add_slide(self, mock_oauth_class, mock_slides_service):
        """Test adding a slide."""
        mock_oauth_class.return_value.get_service.return_value = mock_slides_service

        service = SlidesService()
        result = await service.add_slide(
            presentation_id="pres1",
            insertion_index=1
        )

        assert 'replies' in result
        mock_slides_service.presentations().batchUpdate.assert_called_once()

    @patch('src.services.slides_service.OAuthHandler')
    async def test_update_slide(self, mock_oauth_class, mock_slides_service):
        """Test updating slide content."""
        mock_oauth_class.return_value.get_service.return_value = mock_slides_service

        service = SlidesService()
        requests = [
            {
                'createShape': {
                    'objectId': 'shape1',
                    'shapeType': 'TEXT_BOX'
                }
            }
        ]
        result = await service.update_slide(
            presentation_id="pres1",
            requests=requests
        )

        assert 'replies' in result
        mock_slides_service.presentations().batchUpdate.assert_called_once()

    @patch('src.services.slides_service.OAuthHandler')
    async def test_delete_presentation(self, mock_oauth_class, mock_drive_service):
        """Test presentation deletion."""
        mock_oauth_class.return_value.get_service.return_value = mock_drive_service
        mock_drive_service.files().delete().execute.return_value = None

        service = SlidesService()
        await service.delete_presentation(presentation_id="pres1")

        mock_drive_service.files().delete.assert_called_once()

    @patch('src.services.slides_service.OAuthHandler')
    async def test_error_handling(self, mock_oauth_class, mock_slides_service):
        """Test error handling."""
        from src.utils.error_handler import GoogleWorkspaceError

        mock_oauth_class.return_value.get_service.return_value = mock_slides_service
        mock_slides_service.presentations().get().execute.side_effect = Exception("API Error")

        service = SlidesService()

        with pytest.raises(GoogleWorkspaceError):
            await service.read_presentation(presentation_id="invalid")
