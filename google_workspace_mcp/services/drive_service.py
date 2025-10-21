"""Google Drive service implementation."""

import io
from typing import Any, Dict, List, Optional
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from ..auth.oauth_handler import get_oauth_handler
from ..utils.logger import setup_logger
from ..utils.error_handler import with_error_handling, ResourceNotFoundError
from ..utils.rate_limiter import rate_limited_call
from ..utils.cache import cached_call, cache_key

logger = setup_logger(__name__)


class DriveService:
    """Google Drive service wrapper."""

    def __init__(self):
        """Initialize Drive service."""
        self.oauth = get_oauth_handler()
        self._service = None

    @property
    def service(self):
        """Get or create Drive service instance."""
        if self._service is None:
            self._service = self.oauth.get_service('drive', 'v3')
        return self._service

    @with_error_handling
    async def search_files(
        self,
        query: Optional[str] = None,
        folder_id: Optional[str] = None,
        file_type: Optional[str] = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """Search for files in Drive.

        Args:
            query: Search query string
            folder_id: Limit search to specific folder
            file_type: Filter by MIME type
            max_results: Maximum number of results

        Returns:
            List of file metadata dictionaries
        """
        # Build query
        query_parts = []
        if query:
            query_parts.append(f"name contains '{query}'")
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")
        if file_type:
            query_parts.append(f"mimeType='{file_type}'")

        q = " and ".join(query_parts) if query_parts else None

        async def _search():
            results = self.service.files().list(
                q=q,
                pageSize=min(max_results, 1000),
                fields="files(id, name, mimeType, modifiedTime, size, parents)"
            ).execute()

            files = results.get('files', [])
            logger.info(f"Found {len(files)} files")
            return files

        cache_k = cache_key("search", query, folder_id, file_type, max_results)
        return await rate_limited_call("drive", cached_call, "drive", cache_k, _search)

    @with_error_handling
    async def read_file(
        self,
        file_id: str,
        mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Read file content from Drive.

        Args:
            file_id: File ID
            mime_type: Export MIME type for Google Docs files

        Returns:
            Dictionary with file metadata and content
        """
        async def _read():
            # Get file metadata
            file_meta = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, modifiedTime, size"
            ).execute()

            # Get file content
            if mime_type or 'google-apps' in file_meta['mimeType']:
                # Export Google Workspace file
                export_mime = mime_type or 'text/plain'
                content = self.service.files().export(
                    fileId=file_id,
                    mimeType=export_mime
                ).execute()
            else:
                # Download binary file
                request = self.service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)

                done = False
                while not done:
                    status, done = downloader.next_chunk()

                content = fh.getvalue()

            logger.info(f"Read file: {file_meta['name']}")
            return {
                "metadata": file_meta,
                "content": content if isinstance(content, str) else content.decode('utf-8', errors='ignore')
            }

        cache_k = cache_key("read", file_id, mime_type)
        return await rate_limited_call("drive", cached_call, "drive", cache_k, _read)

    @with_error_handling
    async def create_file(
        self,
        name: str,
        content: str = "",
        mime_type: str = "text/plain",
        folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create new file in Drive.

        Args:
            name: File name
            content: File content
            mime_type: MIME type
            folder_id: Parent folder ID

        Returns:
            Created file metadata
        """
        async def _create():
            file_metadata = {'name': name}
            if folder_id:
                file_metadata['parents'] = [folder_id]

            media = MediaFileUpload(
                io.BytesIO(content.encode()),
                mimetype=mime_type,
                resumable=True
            )

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, mimeType, webViewLink'
            ).execute()

            logger.info(f"Created file: {file['name']} ({file['id']})")
            return file

        return await rate_limited_call("drive", _create)

    @with_error_handling
    async def update_file(
        self,
        file_id: str,
        content: Optional[str] = None,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update existing file.

        Args:
            file_id: File ID
            content: New content (optional)
            name: New name (optional)

        Returns:
            Updated file metadata
        """
        async def _update():
            file_metadata = {}
            if name:
                file_metadata['name'] = name

            kwargs = {'fileId': file_id, 'fields': 'id, name, modifiedTime'}

            if file_metadata:
                kwargs['body'] = file_metadata

            if content:
                kwargs['media_body'] = MediaFileUpload(
                    io.BytesIO(content.encode()),
                    resumable=True
                )

            file = self.service.files().update(**kwargs).execute()
            logger.info(f"Updated file: {file_id}")
            return file

        return await rate_limited_call("drive", _update)

    @with_error_handling
    async def delete_file(self, file_id: str) -> bool:
        """Delete file from Drive.

        Args:
            file_id: File ID

        Returns:
            True if deleted successfully
        """
        async def _delete():
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"Deleted file: {file_id}")
            return True

        return await rate_limited_call("drive", _delete)

    @with_error_handling
    async def upload_file(
        self,
        local_path: str,
        name: Optional[str] = None,
        folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload local file to Drive.

        Args:
            local_path: Local file path
            name: Name for uploaded file (defaults to filename)
            folder_id: Parent folder ID

        Returns:
            Uploaded file metadata
        """
        import os
        import mimetypes

        async def _upload():
            file_name = name or os.path.basename(local_path)
            mime_type = mimetypes.guess_type(local_path)[0] or 'application/octet-stream'

            file_metadata = {'name': file_name}
            if folder_id:
                file_metadata['parents'] = [folder_id]

            media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, mimeType, size, webViewLink'
            ).execute()

            logger.info(f"Uploaded file: {file['name']} ({file['id']})")
            return file

        return await rate_limited_call("drive", _upload)

    @with_error_handling
    async def download_file(
        self,
        file_id: str,
        local_path: str,
        mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Download file from Drive to local system.

        Args:
            file_id: File ID
            local_path: Local path to save file
            mime_type: Export MIME type for Google Docs files

        Returns:
            Dictionary with download info
        """
        async def _download():
            # Get file metadata
            file_meta = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size"
            ).execute()

            # Download content
            if mime_type or 'google-apps' in file_meta['mimeType']:
                export_mime = mime_type or 'application/pdf'
                content = self.service.files().export(
                    fileId=file_id,
                    mimeType=export_mime
                ).execute()
            else:
                request = self.service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)

                done = False
                while not done:
                    status, done = downloader.next_chunk()

                content = fh.getvalue()

            # Write to local file
            mode = 'w' if isinstance(content, str) else 'wb'
            with open(local_path, mode) as f:
                f.write(content)

            logger.info(f"Downloaded file to: {local_path}")
            return {
                "file_id": file_id,
                "name": file_meta['name'],
                "local_path": local_path,
                "size": len(content)
            }

        return await rate_limited_call("drive", _download)

    @with_error_handling
    async def list_shared_drives(self, max_results: int = 100) -> List[Dict[str, Any]]:
        """List shared drives (Team Drives).

        Args:
            max_results: Maximum number of results

        Returns:
            List of shared drive metadata
        """
        async def _list():
            results = self.service.drives().list(
                pageSize=min(max_results, 100),
                fields="drives(id, name)"
            ).execute()

            drives = results.get('drives', [])
            logger.info(f"Found {len(drives)} shared drives")
            return drives

        cache_k = cache_key("shared_drives", max_results)
        return await rate_limited_call("drive", cached_call, "drive", cache_k, _list)
