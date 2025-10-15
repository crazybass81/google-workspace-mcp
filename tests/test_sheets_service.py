"""Tests for Sheets service."""

import pytest
from unittest.mock import Mock, patch
from src.services.sheets_service import SheetsService


@pytest.mark.asyncio
class TestSheetsService:
    """Test Sheets service operations."""

    @patch('src.services.sheets_service.OAuthHandler')
    async def test_create_spreadsheet(self, mock_oauth_class, mock_sheets_service):
        """Test spreadsheet creation."""
        mock_oauth_class.return_value.get_service.return_value = mock_sheets_service

        service = SheetsService()
        result = await service.create_spreadsheet(title="Test Sheet")

        assert result['spreadsheetId'] == 'sheet1'
        assert result['properties']['title'] == 'Test Sheet'
        mock_sheets_service.spreadsheets().create.assert_called_once()

    @patch('src.services.sheets_service.OAuthHandler')
    async def test_read_range(self, mock_oauth_class, mock_sheets_service):
        """Test reading range data."""
        mock_oauth_class.return_value.get_service.return_value = mock_sheets_service

        service = SheetsService()
        result = await service.read_range(
            spreadsheet_id="sheet1",
            range_name="Sheet1!A1:B2"
        )

        assert result['range'] == 'Sheet1!A1:B2'
        assert len(result['values']) == 2
        assert result['values'][0] == ['A1', 'B1']
        mock_sheets_service.spreadsheets().values().get.assert_called_once()

    @patch('src.services.sheets_service.OAuthHandler')
    async def test_update_range(self, mock_oauth_class, mock_sheets_service):
        """Test updating range data."""
        mock_oauth_class.return_value.get_service.return_value = mock_sheets_service

        service = SheetsService()
        result = await service.update_range(
            spreadsheet_id="sheet1",
            range_name="Sheet1!A1:B2",
            values=[['X1', 'Y1'], ['X2', 'Y2']]
        )

        assert result['updatedCells'] == 4
        assert result['updatedRows'] == 2
        mock_sheets_service.spreadsheets().values().update.assert_called_once()

    @patch('src.services.sheets_service.OAuthHandler')
    async def test_batch_update(self, mock_oauth_class, mock_sheets_service):
        """Test batch update operations."""
        mock_oauth_class.return_value.get_service.return_value = mock_sheets_service

        service = SheetsService()
        requests = [
            {
                'updateCells': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'fields': 'userEnteredValue'
                }
            }
        ]
        result = await service.batch_update(
            spreadsheet_id="sheet1",
            requests=requests
        )

        assert 'replies' in result
        mock_sheets_service.spreadsheets().batchUpdate.assert_called_once()

    @patch('src.services.sheets_service.OAuthHandler')
    async def test_delete_spreadsheet(self, mock_oauth_class, mock_drive_service):
        """Test spreadsheet deletion."""
        mock_oauth_class.return_value.get_service.return_value = mock_drive_service
        mock_drive_service.files().delete().execute.return_value = None

        service = SheetsService()
        await service.delete_spreadsheet(spreadsheet_id="sheet1")

        mock_drive_service.files().delete.assert_called_once()

    @patch('src.services.sheets_service.OAuthHandler')
    async def test_error_handling(self, mock_oauth_class, mock_sheets_service):
        """Test error handling."""
        from src.utils.error_handler import GoogleWorkspaceError

        mock_oauth_class.return_value.get_service.return_value = mock_sheets_service
        mock_sheets_service.spreadsheets().values().get().execute.side_effect = Exception("API Error")

        service = SheetsService()

        with pytest.raises(GoogleWorkspaceError):
            await service.read_range(
                spreadsheet_id="invalid",
                range_name="Sheet1!A1"
            )
