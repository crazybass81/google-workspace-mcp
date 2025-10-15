"""Google Forms service implementation."""

from typing import Any, Dict, List, Optional
from ..auth.oauth_handler import get_oauth_handler
from ..utils.logger import setup_logger
from ..utils.error_handler import with_error_handling
from ..utils.rate_limiter import rate_limited_call
from ..utils.cache import cached_call, cache_key

logger = setup_logger(__name__)


class FormsService:
    """Google Forms service wrapper."""

    def __init__(self):
        self.oauth = get_oauth_handler()
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = self.oauth.get_service('forms', 'v1')
        return self._service

    @with_error_handling
    async def create_form(self, title: str, document_title: Optional[str] = None) -> Dict[str, Any]:
        """Create new Google Form."""
        async def _create():
            form = {
                'info': {
                    'title': title,
                    'documentTitle': document_title or title
                }
            }
            result = self.service.forms().create(body=form).execute()
            logger.info(f"Created form: {result['info']['title']} ({result['formId']})")
            return result

        return await rate_limited_call("forms", _create)

    @with_error_handling
    async def read_form(self, form_id: str) -> Dict[str, Any]:
        """Read Google Form structure."""
        async def _read():
            form = self.service.forms().get(formId=form_id).execute()

            items_info = []
            for item in form.get('items', []):
                item_info = {
                    'item_id': item['itemId'],
                    'title': item.get('title', ''),
                    'question_type': list(item.get('questionItem', {}).get('question', {}).keys())[0] if 'questionItem' in item else 'other'
                }
                items_info.append(item_info)

            logger.info(f"Read form: {form['info']['title']}")
            return {
                "form_id": form['formId'],
                "title": form['info']['title'],
                "items": items_info,
                "item_count": len(items_info)
            }

        cache_k = cache_key("forms_read", form_id)
        return await rate_limited_call("forms", cached_call, "forms", cache_k, _read)

    @with_error_handling
    async def update_form(
        self,
        form_id: str,
        requests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Update form structure and questions."""
        async def _update():
            body = {'requests': requests}
            result = self.service.forms().batchUpdate(
                formId=form_id,
                body=body
            ).execute()

            logger.info(f"Updated form: {form_id}")
            return result

        return await rate_limited_call("forms", _update)

    @with_error_handling
    async def delete_form(self, form_id: str) -> bool:
        """Delete Google Form (via Drive API)."""
        from .drive_service import DriveService
        drive = DriveService()
        return await drive.delete_file(form_id)

    @with_error_handling
    async def get_responses(self, form_id: str) -> Dict[str, Any]:
        """Get form responses."""
        async def _get_responses():
            responses = self.service.forms().responses().list(formId=form_id).execute()
            response_list = responses.get('responses', [])

            logger.info(f"Retrieved {len(response_list)} responses from form: {form_id}")
            return {
                "form_id": form_id,
                "response_count": len(response_list),
                "responses": response_list
            }

        cache_k = cache_key("forms_responses", form_id)
        return await rate_limited_call("forms", cached_call, "forms", cache_k, _get_responses, ttl=60)
