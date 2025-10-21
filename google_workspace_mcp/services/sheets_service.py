"""Google Sheets service implementation."""

from typing import Any, Dict, List, Optional
from ..auth.oauth_handler import get_oauth_handler
from ..utils.logger import setup_logger
from ..utils.error_handler import with_error_handling
from ..utils.rate_limiter import rate_limited_call
from ..utils.cache import cached_call, cache_key

logger = setup_logger(__name__)


class SheetsService:
    """Google Sheets service wrapper."""

    def __init__(self):
        self.oauth = get_oauth_handler()
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = self.oauth.get_service('sheets', 'v4')
        return self._service

    @with_error_handling
    async def create_spreadsheet(self, title: str) -> Dict[str, Any]:
        """Create new Google Sheets spreadsheet."""
        async def _create():
            spreadsheet = {
                'properties': {'title': title}
            }
            result = self.service.spreadsheets().create(body=spreadsheet).execute()
            logger.info(f"Created spreadsheet: {result['properties']['title']} ({result['spreadsheetId']})")
            return result

        return await rate_limited_call("sheets", _create)

    @with_error_handling
    async def read_range(
        self,
        spreadsheet_id: str,
        range_name: str
    ) -> Dict[str, Any]:
        """Read data from spreadsheet range."""
        async def _read():
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()

            values = result.get('values', [])
            logger.info(f"Read {len(values)} rows from {range_name}")
            return {
                "spreadsheet_id": spreadsheet_id,
                "range": range_name,
                "values": values
            }

        cache_k = cache_key("sheets_read", spreadsheet_id, range_name)
        return await rate_limited_call("sheets", cached_call, "sheets", cache_k, _read)

    @with_error_handling
    async def update_range(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]]
    ) -> Dict[str, Any]:
        """Update spreadsheet range with values."""
        async def _update():
            body = {'values': values}
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()

            logger.info(f"Updated {result.get('updatedCells', 0)} cells in {range_name}")
            return result

        return await rate_limited_call("sheets", _update)

    @with_error_handling
    async def delete_spreadsheet(self, spreadsheet_id: str) -> bool:
        """Delete Google Sheets spreadsheet (via Drive API)."""
        from .drive_service import DriveService
        drive = DriveService()
        return await drive.delete_file(spreadsheet_id)

    @with_error_handling
    async def batch_update(
        self,
        spreadsheet_id: str,
        requests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform batch update operations."""
        async def _batch():
            body = {'requests': requests}
            result = self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()

            logger.info(f"Batch updated spreadsheet: {spreadsheet_id}")
            return result

        return await rate_limited_call("sheets", _batch)
