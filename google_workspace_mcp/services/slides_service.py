"""Google Slides service implementation."""

from typing import Any, Dict, List, Optional
from ..auth.oauth_handler import get_oauth_handler
from ..utils.logger import setup_logger
from ..utils.error_handler import with_error_handling
from ..utils.rate_limiter import rate_limited_call
from ..utils.cache import cached_call, cache_key

logger = setup_logger(__name__)


class SlidesService:
    """Google Slides service wrapper."""

    def __init__(self):
        self.oauth = get_oauth_handler()
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = self.oauth.get_service('slides', 'v1')
        return self._service

    @with_error_handling
    async def create_presentation(self, title: str) -> Dict[str, Any]:
        """Create new Google Slides presentation."""
        async def _create():
            presentation = {
                'title': title
            }
            result = self.service.presentations().create(body=presentation).execute()
            logger.info(f"Created presentation: {result['title']} ({result['presentationId']})")
            return result

        return await rate_limited_call("slides", _create)

    @with_error_handling
    async def read_presentation(self, presentation_id: str) -> Dict[str, Any]:
        """Read Google Slides presentation structure."""
        async def _read():
            presentation = self.service.presentations().get(
                presentationId=presentation_id
            ).execute()

            slides_info = []
            for slide in presentation.get('slides', []):
                slide_info = {
                    'slide_id': slide['objectId'],
                    'page_elements': len(slide.get('pageElements', []))
                }
                slides_info.append(slide_info)

            logger.info(f"Read presentation: {presentation['title']}")
            return {
                "presentation_id": presentation['presentationId'],
                "title": presentation['title'],
                "slides": slides_info,
                "slide_count": len(slides_info)
            }

        cache_k = cache_key("slides_read", presentation_id)
        return await rate_limited_call("slides", cached_call, "slides", cache_k, _read)

    @with_error_handling
    async def add_slide(
        self,
        presentation_id: str,
        insertion_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """Add new slide to presentation."""
        async def _add():
            requests = [{
                'createSlide': {
                    'insertionIndex': insertion_index
                }
            }]

            result = self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()

            logger.info(f"Added slide to presentation: {presentation_id}")
            return result

        return await rate_limited_call("slides", _add)

    @with_error_handling
    async def update_slide(
        self,
        presentation_id: str,
        requests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Update slide content."""
        async def _update():
            result = self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()

            logger.info(f"Updated slides in presentation: {presentation_id}")
            return result

        return await rate_limited_call("slides", _update)

    @with_error_handling
    async def delete_presentation(self, presentation_id: str) -> bool:
        """Delete Google Slides presentation (via Drive API)."""
        from .drive_service import DriveService
        drive = DriveService()
        return await drive.delete_file(presentation_id)
