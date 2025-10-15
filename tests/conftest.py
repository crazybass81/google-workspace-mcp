"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


@pytest.fixture
def mock_credentials():
    """Mock Google OAuth credentials."""
    creds = Mock(spec=Credentials)
    creds.valid = True
    creds.expired = False
    creds.token = "mock_token"
    return creds


@pytest.fixture
def mock_drive_service():
    """Mock Google Drive service."""
    service = MagicMock()

    # Mock files().list()
    service.files().list().execute.return_value = {
        'files': [
            {
                'id': 'file1',
                'name': 'test.txt',
                'mimeType': 'text/plain'
            }
        ]
    }

    # Mock files().get()
    service.files().get().execute.return_value = {
        'id': 'file1',
        'name': 'test.txt',
        'mimeType': 'text/plain'
    }

    # Mock files().get_media()
    service.files().get_media().execute.return_value = b'test content'

    # Mock files().create()
    service.files().create().execute.return_value = {
        'id': 'new_file',
        'name': 'new.txt'
    }

    # Mock files().update()
    service.files().update().execute.return_value = {
        'id': 'file1',
        'name': 'updated.txt'
    }

    # Mock drives().list()
    service.drives().list().execute.return_value = {
        'drives': [
            {
                'id': 'drive1',
                'name': 'Shared Drive'
            }
        ]
    }

    return service


@pytest.fixture
def mock_docs_service():
    """Mock Google Docs service."""
    service = MagicMock()

    # Mock documents().create()
    service.documents().create().execute.return_value = {
        'documentId': 'doc1',
        'title': 'Test Document'
    }

    # Mock documents().get()
    service.documents().get().execute.return_value = {
        'documentId': 'doc1',
        'title': 'Test Document',
        'body': {
            'content': [
                {
                    'paragraph': {
                        'elements': [
                            {'textRun': {'content': 'Test content'}}
                        ]
                    }
                }
            ]
        }
    }

    # Mock documents().batchUpdate()
    service.documents().batchUpdate().execute.return_value = {}

    return service


@pytest.fixture
def mock_sheets_service():
    """Mock Google Sheets service."""
    service = MagicMock()

    # Mock spreadsheets().create()
    service.spreadsheets().create().execute.return_value = {
        'spreadsheetId': 'sheet1',
        'properties': {'title': 'Test Sheet'}
    }

    # Mock spreadsheets().values().get()
    service.spreadsheets().values().get().execute.return_value = {
        'range': 'Sheet1!A1:B2',
        'values': [
            ['A1', 'B1'],
            ['A2', 'B2']
        ]
    }

    # Mock spreadsheets().values().update()
    service.spreadsheets().values().update().execute.return_value = {
        'updatedCells': 4,
        'updatedRows': 2,
        'updatedColumns': 2
    }

    # Mock spreadsheets().batchUpdate()
    service.spreadsheets().batchUpdate().execute.return_value = {
        'replies': []
    }

    return service


@pytest.fixture
def mock_slides_service():
    """Mock Google Slides service."""
    service = MagicMock()

    # Mock presentations().create()
    service.presentations().create().execute.return_value = {
        'presentationId': 'pres1',
        'title': 'Test Presentation'
    }

    # Mock presentations().get()
    service.presentations().get().execute.return_value = {
        'presentationId': 'pres1',
        'title': 'Test Presentation',
        'slides': [
            {
                'objectId': 'slide1',
                'pageElements': []
            }
        ]
    }

    # Mock presentations().batchUpdate()
    service.presentations().batchUpdate().execute.return_value = {
        'replies': [
            {'createSlide': {'objectId': 'new_slide'}}
        ]
    }

    return service


@pytest.fixture
def mock_forms_service():
    """Mock Google Forms service."""
    service = MagicMock()

    # Mock forms().create()
    service.forms().create().execute.return_value = {
        'formId': 'form1',
        'info': {'title': 'Test Form'}
    }

    # Mock forms().get()
    service.forms().get().execute.return_value = {
        'formId': 'form1',
        'info': {'title': 'Test Form'},
        'items': []
    }

    # Mock forms().batchUpdate()
    service.forms().batchUpdate().execute.return_value = {}

    # Mock forms().responses().list()
    service.forms().responses().list().execute.return_value = {
        'responses': []
    }

    return service


@pytest.fixture
def mock_gmail_service():
    """Mock Gmail service."""
    service = MagicMock()

    # Mock users().messages().list()
    service.users().messages().list().execute.return_value = {
        'messages': [
            {'id': 'msg1', 'threadId': 'thread1'}
        ]
    }

    # Mock users().messages().get()
    service.users().messages().get().execute.return_value = {
        'id': 'msg1',
        'threadId': 'thread1',
        'labelIds': ['INBOX'],
        'payload': {
            'headers': [
                {'name': 'From', 'value': 'test@example.com'},
                {'name': 'Subject', 'value': 'Test Subject'},
                {'name': 'Date', 'value': '2024-01-01'}
            ],
            'body': {'data': 'VGVzdCBib2R5'}  # "Test body" in base64
        }
    }

    # Mock users().messages().send()
    service.users().messages().send().execute.return_value = {
        'id': 'sent1',
        'threadId': 'thread1'
    }

    # Mock users().labels().list()
    service.users().labels().list().execute.return_value = {
        'labels': [
            {'id': 'INBOX', 'name': 'INBOX'},
            {'id': 'SENT', 'name': 'SENT'}
        ]
    }

    # Mock users().messages().modify()
    service.users().messages().modify().execute.return_value = {
        'id': 'msg1',
        'labelIds': ['INBOX', 'UNREAD']
    }

    return service


@pytest.fixture
def mock_oauth_handler(mock_credentials):
    """Mock OAuth handler."""
    from src.auth.oauth_handler import OAuthHandler

    handler = Mock(spec=OAuthHandler)
    handler.authenticate.return_value = mock_credentials
    handler.get_service = Mock()

    return handler
