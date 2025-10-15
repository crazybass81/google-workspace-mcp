# Google Workspace MCP Server - Test Suite

## Overview

Comprehensive test suite for Google Workspace MCP Server with **34 MCP tools** across 6 services.

## Test Structure

```
tests/
├── conftest.py              # Pytest fixtures and mock configurations
├── test_drive_service.py    # Drive service unit tests (8 tools)
├── test_docs_service.py     # Docs service unit tests (4 tools)
├── test_sheets_service.py   # Sheets service unit tests (5 tools)
├── test_slides_service.py   # Slides service unit tests (5 tools)
├── test_forms_service.py    # Forms service unit tests (5 tools)
├── test_gmail_service.py    # Gmail service unit tests (7 tools)
└── test_integration.py      # Integration and MCP tool tests
```

## Test Coverage

### Service Tests (Unit)
- **Drive Service**: 8 test cases covering all CRUD operations + uploads/downloads
- **Docs Service**: 4 test cases covering document lifecycle
- **Sheets Service**: 5 test cases covering spreadsheet operations
- **Slides Service**: 5 test cases covering presentation management
- **Forms Service**: 5 test cases covering form creation and responses
- **Gmail Service**: 8 test cases covering email operations and labels

### Integration Tests
- **Tool Registration**: Verifies all 34 MCP tools are properly registered
- **Tool Schemas**: Validates all tool input schemas
- **Tool Handlers**: Tests each service's tool handler integration
- **Error Handling**: Verifies graceful error handling across all tools
- **Utilities**: Tests logger, error handler, rate limiter, and cache

## Running Tests

### Run All Tests
```bash
python3 -m pytest tests/ -v
```

### Run Specific Service Tests
```bash
# Drive service tests
python3 -m pytest tests/test_drive_service.py -v

# Docs service tests
python3 -m pytest tests/test_docs_service.py -v

# Gmail service tests
python3 -m pytest tests/test_gmail_service.py -v
```

### Run Integration Tests
```bash
python3 -m pytest tests/test_integration.py -v
```

### Run with Coverage Report
```bash
python3 -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
```

### Run Specific Test
```bash
python3 -m pytest tests/test_integration.py::TestMCPIntegration::test_all_tools_registered -v
```

## Test Results Summary

### Expected Test Count
- **Drive Service**: 8 tests
- **Docs Service**: 5 tests
- **Sheets Service**: 6 tests
- **Slides Service**: 6 tests
- **Forms Service**: 6 tests
- **Gmail Service**: 9 tests
- **Integration**: 12 tests
- **Total**: ~50+ test cases

### Code Coverage
Current coverage focuses on:
- ✅ Tool registration and schemas (100%)
- ✅ Error handling integration (70%+)
- ✅ Utility modules (35-94%)
- ⚠️ Service implementations (24-43% - requires real Google API for full coverage)

Note: Service coverage is lower because tests use mocks. Full coverage requires integration testing with real Google APIs.

## Mocking Strategy

All tests use comprehensive mocks to avoid requiring:
- Google Cloud Console credentials
- OAuth authentication
- Live Google API calls
- Network connectivity

Mocks are configured in `conftest.py` with realistic return values.

## Test Fixtures

### Available Fixtures
- `mock_credentials`: Mock OAuth credentials
- `mock_drive_service`: Mock Google Drive API service
- `mock_docs_service`: Mock Google Docs API service
- `mock_sheets_service`: Mock Google Sheets API service
- `mock_slides_service`: Mock Google Slides API service
- `mock_forms_service`: Mock Google Forms API service
- `mock_gmail_service`: Mock Gmail API service
- `mock_oauth_handler`: Mock OAuth authentication handler

## Writing New Tests

### Test Template
```python
import pytest
from unittest.mock import Mock, patch
from src.services.your_service import YourService

@pytest.mark.asyncio
class TestYourService:
    """Test Your service operations."""

    @patch('src.services.your_service.OAuthHandler')
    async def test_your_operation(self, mock_oauth_class, mock_your_service):
        """Test your operation."""
        mock_oauth_class.return_value.get_service.return_value = mock_your_service

        service = YourService()
        result = await service.your_operation(param="value")

        assert result['expected_key'] == 'expected_value'
        mock_your_service.your_method().call.assert_called_once()
```

## Continuous Integration

Tests are designed to run without external dependencies, making them suitable for:
- Local development
- CI/CD pipelines
- Pre-commit hooks
- Automated testing

## Known Limitations

1. **Service Coverage**: Tests use mocks, so actual Google API behavior isn't validated
2. **Network Operations**: Upload/download operations are mocked
3. **OAuth Flow**: Authentication flow isn't tested end-to-end
4. **Rate Limiting**: Rate limiter tests don't test actual delays
5. **Caching**: Cache tests don't test TTL expiration

For full integration testing with real Google APIs, additional test configuration is needed.

## Troubleshooting

### Import Errors
```bash
# Ensure src package is in Python path
export PYTHONPATH="${PYTHONPATH}:/Users/t/google-workspace-mcp"
```

### Async Test Errors
```bash
# Install pytest-asyncio
pip3 install pytest-asyncio
```

### Coverage Missing
```bash
# Install pytest-cov
pip3 install pytest-cov
```

## Future Enhancements

- [ ] Add integration tests with real Google APIs (optional, requires credentials)
- [ ] Add performance benchmarking tests
- [ ] Add stress testing for rate limiter
- [ ] Add property-based testing with hypothesis
- [ ] Add mutation testing with mutmut
- [ ] Add contract testing for MCP protocol compliance
