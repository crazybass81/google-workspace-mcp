"""Tests for Sheets tools handlers."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from mcp.types import TextContent
from src.tools.sheets_tools import (
    handle_sheets_tool,
    SHEETS_TOOLS
)


@pytest.mark.asyncio
class TestSheetsToolsRegistration:
    """Test Sheets tools registration and schemas."""

    def test_all_sheets_tools_registered(self):
        """Test that all 5 Sheets tools are registered."""
        assert len(SHEETS_TOOLS) == 5

        tool_names = [tool.name for tool in SHEETS_TOOLS]
        assert 'sheets_create' in tool_names
        assert 'sheets_read' in tool_names
        assert 'sheets_update' in tool_names
        assert 'sheets_delete' in tool_names
        assert 'sheets_batch_update' in tool_names

    def test_sheets_tools_schemas(self):
        """Test that all Sheets tools have valid schemas."""
        for tool in SHEETS_TOOLS:
            assert tool.name is not None
            assert tool.description is not None
            assert tool.inputSchema is not None
            assert 'type' in tool.inputSchema
            assert tool.inputSchema['type'] == 'object'
            assert 'properties' in tool.inputSchema


@pytest.mark.asyncio
class TestSheetsToolHandlers:
    """Test Sheets tool handlers with proper mocking."""

    @patch('src.tools.sheets_tools.sheets_service')
    async def test_create_handler(self, mock_service):
        """Test sheets_create tool handler."""
        mock_service.create_spreadsheet = AsyncMock(return_value={
            'spreadsheetId': 'sheet1',
            'properties': {'title': 'Test Sheet'}
        })

        result = await handle_sheets_tool('sheets_create', {'title': 'Test Sheet'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'sheet1' in result[0].text
        mock_service.create_spreadsheet.assert_called_once_with(title='Test Sheet')

    @patch('src.tools.sheets_tools.sheets_service')
    async def test_read_handler(self, mock_service):
        """Test sheets_read tool handler."""
        mock_service.read_values = AsyncMock(return_value={
            'values': [['Name', 'Age'], ['Alice', '30']]
        })

        result = await handle_sheets_tool('sheets_read', {
            'spreadsheet_id': 'sheet1',
            'range': 'A1:B2'
        })

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'Alice' in result[0].text
        mock_service.read_values.assert_called_once()

    @patch('src.tools.sheets_tools.sheets_service')
    async def test_update_handler(self, mock_service):
        """Test sheets_update tool handler."""
        mock_service.update_values = AsyncMock(return_value={
            'updatedCells': 4
        })

        result = await handle_sheets_tool('sheets_update', {
            'spreadsheet_id': 'sheet1',
            'range': 'A1:B2',
            'values': [['Name', 'Age']]
        })

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'updated' in result[0].text.lower()
        mock_service.update_values.assert_called_once()

    @patch('src.tools.sheets_tools.sheets_service')
    async def test_delete_handler(self, mock_service):
        """Test sheets_delete tool handler."""
        mock_service.delete_spreadsheet = AsyncMock(return_value={'success': True})

        result = await handle_sheets_tool('sheets_delete', {'spreadsheet_id': 'sheet1'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'successfully' in result[0].text.lower()
        mock_service.delete_spreadsheet.assert_called_once_with(spreadsheet_id='sheet1')

    @patch('src.tools.sheets_tools.sheets_service')
    async def test_batch_update_handler(self, mock_service):
        """Test sheets_batch_update tool handler."""
        mock_service.batch_update = AsyncMock(return_value={
            'replies': [],
            'updatedSpreadsheet': {'spreadsheetId': 'sheet1'}
        })

        result = await handle_sheets_tool('sheets_batch_update', {
            'spreadsheet_id': 'sheet1',
            'requests': [{}]
        })

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'sheet1' in result[0].text
        mock_service.batch_update.assert_called_once()

    @patch('src.tools.sheets_tools.sheets_service')
    async def test_error_handling(self, mock_service):
        """Test error handling in Sheets tool handlers."""
        from src.utils.error_handler import GoogleWorkspaceError

        mock_service.create_spreadsheet = AsyncMock(
            side_effect=GoogleWorkspaceError("API Error", "Test error")
        )

        result = await handle_sheets_tool('sheets_create', {'title': 'Test'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'Error' in result[0].text

    async def test_invalid_tool_name(self):
        """Test handling of invalid tool name."""
        result = await handle_sheets_tool('invalid_tool', {})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'Unknown' in result[0].text or 'Error' in result[0].text
