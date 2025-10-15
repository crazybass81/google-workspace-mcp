"""Google Drive API Client"""
import os
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes required for Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class DriveClient:
    """Client for Google Drive API operations"""

    def __init__(self):
        self.config_dir = Path.home() / 'google-workspace-mcp' / 'config'
        self.credentials_file = self.config_dir / 'credentials.json'
        self.token_file = self.config_dir / 'token.pickle'
        self.service = None

    def authenticate(self):
        """Authenticate with Google Drive API"""
        creds = None

        # Load existing token if available
        if self.token_file.exists():
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)

        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_file), SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials for future use
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('drive', 'v3', credentials=creds)
        return self.service

    def search_files(self, query=None, max_results=10, order_by='modifiedTime desc'):
        """Search files in Google Drive

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            order_by: Sort order (default: recent first)

        Returns:
            List of file dictionaries
        """
        if not self.service:
            self.authenticate()

        # Build search query
        search_query = []
        if query:
            search_query.append(f"name contains '{query}'")

        # Exclude trashed files
        search_query.append("trashed = false")

        q = " and ".join(search_query)

        results = self.service.files().list(
            q=q,
            pageSize=max_results,
            orderBy=order_by,
            fields="files(id, name, mimeType, modifiedTime, webViewLink, size)"
        ).execute()

        return results.get('files', [])

    def get_recent_files(self, max_results=20):
        """Get recently modified files

        Args:
            max_results: Maximum number of files to return

        Returns:
            List of file dictionaries
        """
        return self.search_files(query=None, max_results=max_results)

    def read_file(self, file_id):
        """Read file content by ID

        Args:
            file_id: Google Drive file ID

        Returns:
            File content as string
        """
        if not self.service:
            self.authenticate()

        # Get file metadata first
        file_metadata = self.service.files().get(fileId=file_id).execute()
        mime_type = file_metadata.get('mimeType', '')

        # Handle Google Docs files
        if mime_type.startswith('application/vnd.google-apps'):
            export_mime_type = 'text/plain'
            content = self.service.files().export(
                fileId=file_id, mimeType=export_mime_type).execute()
            return content.decode('utf-8')
        else:
            # Handle regular files
            content = self.service.files().get_media(fileId=file_id).execute()
            return content.decode('utf-8')
