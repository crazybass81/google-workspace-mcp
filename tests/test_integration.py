"""Integration tests for MCP server."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from mcp.types import TextContent
from src.tools import ALL_TOOLS, handle_drive_tool, handle_docs_tool, \
                      handle_sheets_tool, handle_slides_tool, \
                      handle_forms_tool, handle_gmail_tool


@pytest.mark.asyncio
class TestMCPIntegration:
    """Test MCP tool integration."""

    def test_all_tools_registered(self):
        """Test that all tools are properly registered."""
        assert len(ALL_TOOLS) == 34  # Total expected tools

        tool_names = [tool.name for tool in ALL_TOOLS]

        # Drive tools (8)
        assert 'drive_search_files' in tool_names
        assert 'drive_read_file' in tool_names
        assert 'drive_create_file' in tool_names
        assert 'drive_update_file' in tool_names
        assert 'drive_upload_file' in tool_names
        assert 'drive_download_file' in tool_names
        assert 'drive_delete_file' in tool_names
        assert 'drive_list_shared_drives' in tool_names

        # Docs tools (4)
        assert 'docs_create' in tool_names
        assert 'docs_read' in tool_names
        assert 'docs_update' in tool_names
        assert 'docs_delete' in tool_names

        # Sheets tools (5)
        assert 'sheets_create' in tool_names
        assert 'sheets_read' in tool_names
        assert 'sheets_update' in tool_names
        assert 'sheets_delete' in tool_names
        assert 'sheets_batch_update' in tool_names

        # Slides tools (5)
        assert 'slides_create' in tool_names
        assert 'slides_read' in tool_names
        assert 'slides_add_slide' in tool_names
        assert 'slides_update' in tool_names
        assert 'slides_delete' in tool_names

        # Forms tools (5)
        assert 'forms_create' in tool_names
        assert 'forms_read' in tool_names
        assert 'forms_update' in tool_names
        assert 'forms_delete' in tool_names
        assert 'forms_get_responses' in tool_names

        # Gmail tools (7)
        assert 'gmail_search_messages' in tool_names
        assert 'gmail_read_message' in tool_names
        assert 'gmail_send_message' in tool_names
        assert 'gmail_reply_message' in tool_names
        assert 'gmail_delete_message' in tool_names
        assert 'gmail_list_labels' in tool_names
        assert 'gmail_modify_labels' in tool_names

    def test_tool_schemas(self):
        """Test that all tools have valid schemas."""
        for tool in ALL_TOOLS:
            assert tool.name is not None
            assert tool.description is not None
            assert tool.inputSchema is not None
            assert 'type' in tool.inputSchema
            assert tool.inputSchema['type'] == 'object'
            assert 'properties' in tool.inputSchema

    @patch('src.tools.drive_tools.DriveService')
    async def test_drive_tool_handler(self, mock_service_class):
        """Test Drive tool handler integration."""
        mock_service = AsyncMock()
        mock_service.search_files.return_value = [{'id': 'file1', 'name': 'test.txt'}]
        mock_service_class.return_value = mock_service

        result = await handle_drive_tool('drive_search_files', {'query': 'test'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'file1' in result[0].text

    @patch('src.tools.docs_tools.DocsService')
    async def test_docs_tool_handler(self, mock_service_class):
        """Test Docs tool handler integration."""
        mock_service = AsyncMock()
        mock_service.create_document.return_value = {
            'documentId': 'doc1',
            'title': 'Test Doc'
        }
        mock_service_class.return_value = mock_service

        result = await handle_docs_tool('docs_create', {'title': 'Test Doc'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'doc1' in result[0].text

    @patch('src.tools.sheets_tools.SheetsService')
    async def test_sheets_tool_handler(self, mock_service_class):
        """Test Sheets tool handler integration."""
        mock_service = AsyncMock()
        mock_service.create_spreadsheet.return_value = {
            'spreadsheetId': 'sheet1',
            'properties': {'title': 'Test Sheet'}
        }
        mock_service_class.return_value = mock_service

        result = await handle_sheets_tool('sheets_create', {'title': 'Test Sheet'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'sheet1' in result[0].text

    @patch('src.tools.slides_tools.SlidesService')
    async def test_slides_tool_handler(self, mock_service_class):
        """Test Slides tool handler integration."""
        mock_service = AsyncMock()
        mock_service.create_presentation.return_value = {
            'presentationId': 'pres1',
            'title': 'Test Presentation'
        }
        mock_service_class.return_value = mock_service

        result = await handle_slides_tool('slides_create', {'title': 'Test Presentation'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'pres1' in result[0].text

    @patch('src.tools.forms_tools.FormsService')
    async def test_forms_tool_handler(self, mock_service_class):
        """Test Forms tool handler integration."""
        mock_service = AsyncMock()
        mock_service.create_form.return_value = {
            'formId': 'form1',
            'info': {'title': 'Test Form'}
        }
        mock_service_class.return_value = mock_service

        result = await handle_forms_tool('forms_create', {'title': 'Test Form'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'form1' in result[0].text

    @patch('src.tools.gmail_tools.GmailService')
    async def test_gmail_tool_handler(self, mock_service_class):
        """Test Gmail tool handler integration."""
        mock_service = AsyncMock()
        mock_service.search_messages.return_value = [
            {
                'id': 'msg1',
                'threadId': 'thread1',
                'payload': {
                    'headers': [
                        {'name': 'From', 'value': 'test@example.com'},
                        {'name': 'Subject', 'value': 'Test'}
                    ]
                },
                'snippet': 'Test message'
            }
        ]
        mock_service_class.return_value = mock_service

        result = await handle_gmail_tool('gmail_search_messages', {'query': 'test'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'msg1' in result[0].text

    @patch('src.tools.drive_tools.DriveService')
    async def test_error_handling_integration(self, mock_service_class):
        """Test error handling in tool handlers."""
        from src.utils.error_handler import GoogleWorkspaceError

        mock_service = AsyncMock()
        mock_service.search_files.side_effect = GoogleWorkspaceError(
            "API Error",
            "Test error"
        )
        mock_service_class.return_value = mock_service

        result = await handle_drive_tool('drive_search_files', {'query': 'test'})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert 'Error' in result[0].text
        assert 'API Error' in result[0].text


@pytest.mark.asyncio
class TestUtilities:
    """Test utility modules."""

    def test_logger_setup(self):
        """Test logger configuration."""
        from src.utils.logger import setup_logger

        logger = setup_logger('test')
        assert logger.name == 'test'
        assert logger.level is not None

    def test_error_handler(self):
        """Test error handler utilities."""
        from src.utils.error_handler import GoogleWorkspaceError, handle_google_api_error

        # Test custom error
        error = GoogleWorkspaceError("Test error", "Details")
        assert error.message == "Test error"
        assert error.details == "Details"

        error_dict = error.to_dict()
        assert error_dict['error']['message'] == "Test error"
        assert error_dict['error']['details'] == "Details"
        assert error_dict['error']['type'] == "GoogleWorkspaceError"

        # Test error conversion
        generic_error = Exception("Generic error")
        converted = handle_google_api_error(generic_error)
        assert isinstance(converted, GoogleWorkspaceError)

    def test_rate_limiter(self):
        """Test rate limiter."""
        from src.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(max_requests=10, time_window=60)
        assert limiter.max_requests == 10
        assert limiter.time_window == 60

    def test_cache(self):
        """Test async cache."""
        from src.utils.cache import AsyncCache

        cache = AsyncCache(maxsize=100, ttl=300)
        # AsyncCache stores these internally but doesn't expose as public attributes
        # Just verify the cache was created and stats work
        stats = cache.get_stats()
        assert 'size' in stats
        assert 'hits' in stats
        assert 'misses' in stats
        assert 'hit_rate' in stats
