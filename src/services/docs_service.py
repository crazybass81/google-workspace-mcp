"""Google Docs service implementation."""

from typing import Any, Dict, List, Optional
from ..auth.oauth_handler import get_oauth_handler
from ..utils.logger import setup_logger
from ..utils.error_handler import with_error_handling
from ..utils.rate_limiter import rate_limited_call
from ..utils.cache import cached_call, cache_key

logger = setup_logger(__name__)


class DocsService:
    """Google Docs service wrapper."""

    def __init__(self):
        self.oauth = get_oauth_handler()
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = self.oauth.get_service('docs', 'v1')
        return self._service

    @with_error_handling
    async def create_document(self, title: str) -> Dict[str, Any]:
        """Create new Google Docs document."""
        async def _create():
            doc = self.service.documents().create(body={'title': title}).execute()
            logger.info(f"Created document: {doc['title']} ({doc['documentId']})")
            return doc

        return await rate_limited_call("docs", _create)

    @with_error_handling
    async def read_document(self, document_id: str) -> Dict[str, Any]:
        """Read Google Docs document content."""
        async def _read():
            doc = self.service.documents().get(documentId=document_id).execute()

            # Extract text content
            content = []
            for element in doc.get('body', {}).get('content', []):
                if 'paragraph' in element:
                    for text_run in element['paragraph'].get('elements', []):
                        if 'textRun' in text_run:
                            content.append(text_run['textRun']['content'])

            logger.info(f"Read document: {doc['title']}")
            return {
                "document_id": doc['documentId'],
                "title": doc['title'],
                "content": ''.join(content)
            }

        cache_k = cache_key("docs_read", document_id)
        return await rate_limited_call("docs", cached_call, "docs", cache_k, _read)

    @with_error_handling
    async def update_document(
        self,
        document_id: str,
        text: str,
        index: int = 1
    ) -> Dict[str, Any]:
        """Update Google Docs document content."""
        async def _update():
            requests = [{
                'insertText': {
                    'location': {'index': index},
                    'text': text
                }
            }]

            result = self.service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()

            logger.info(f"Updated document: {document_id}")
            return result

        return await rate_limited_call("docs", _update)

    @with_error_handling
    async def delete_document(self, document_id: str) -> bool:
        """Delete Google Docs document (via Drive API)."""
        from .drive_service import DriveService
        drive = DriveService()
        return await drive.delete_file(document_id)
