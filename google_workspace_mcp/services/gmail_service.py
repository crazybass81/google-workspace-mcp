"""Gmail service implementation."""

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List, Optional
from ..auth.oauth_handler import get_oauth_handler
from ..utils.logger import setup_logger
from ..utils.error_handler import with_error_handling
from ..utils.rate_limiter import rate_limited_call
from ..utils.cache import cached_call, cache_key

logger = setup_logger(__name__)


class GmailService:
    """Gmail service wrapper."""

    def __init__(self):
        self.oauth = get_oauth_handler()
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = self.oauth.get_service('gmail', 'v1')
        return self._service

    @with_error_handling
    async def search_messages(
        self,
        query: str = "",
        max_results: int = 100,
        label_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search for messages in Gmail."""
        async def _search():
            params = {
                'userId': 'me',
                'q': query,
                'maxResults': min(max_results, 500)
            }
            if label_ids:
                params['labelIds'] = label_ids

            results = self.service.users().messages().list(**params).execute()
            messages = results.get('messages', [])

            # Get full message details
            detailed_messages = []
            for msg in messages:
                detail = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'To', 'Subject', 'Date']
                ).execute()
                detailed_messages.append(detail)

            logger.info(f"Found {len(detailed_messages)} messages")
            return detailed_messages

        cache_k = cache_key("gmail_search", query, max_results, label_ids)
        return await rate_limited_call("gmail", cached_call, "gmail", cache_k, _search, ttl=60)

    @with_error_handling
    async def read_message(self, message_id: str) -> Dict[str, Any]:
        """Read full message content."""
        async def _read():
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            # Extract headers
            headers = {}
            for header in message['payload'].get('headers', []):
                headers[header['name']] = header['value']

            # Extract body
            body = ""
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                        body += base64.urlsafe_b64decode(part['body']['data']).decode()
            elif 'body' in message['payload'] and 'data' in message['payload']['body']:
                body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode()

            logger.info(f"Read message: {message_id}")
            return {
                "message_id": message_id,
                "thread_id": message['threadId'],
                "labels": message.get('labelIds', []),
                "snippet": message.get('snippet', ''),
                "headers": headers,
                "body": body
            }

        cache_k = cache_key("gmail_read", message_id)
        return await rate_limited_call("gmail", cached_call, "gmail", cache_k, _read, ttl=300)

    @with_error_handling
    async def send_message(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send new email message."""
        async def _send():
            message = MIMEMultipart()
            message['To'] = to
            message['Subject'] = subject
            if cc:
                message['Cc'] = cc
            if bcc:
                message['Bcc'] = bcc

            message.attach(MIMEText(body, 'plain'))

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            logger.info(f"Sent message: {result['id']}")
            return result

        return await rate_limited_call("gmail", _send)

    @with_error_handling
    async def reply_message(
        self,
        message_id: str,
        body: str
    ) -> Dict[str, Any]:
        """Reply to an existing message."""
        async def _reply():
            # Get original message
            original = await self.read_message(message_id)

            # Create reply
            reply = MIMEText(body)
            reply['To'] = original['headers'].get('From', '')
            reply['Subject'] = 'Re: ' + original['headers'].get('Subject', '')
            reply['In-Reply-To'] = message_id
            reply['References'] = message_id

            raw_reply = base64.urlsafe_b64encode(reply.as_bytes()).decode()

            result = self.service.users().messages().send(
                userId='me',
                body={
                    'raw': raw_reply,
                    'threadId': original['thread_id']
                }
            ).execute()

            logger.info(f"Replied to message: {message_id}")
            return result

        return await rate_limited_call("gmail", _reply)

    @with_error_handling
    async def delete_message(self, message_id: str) -> bool:
        """Delete message (move to trash)."""
        async def _delete():
            self.service.users().messages().trash(
                userId='me',
                id=message_id
            ).execute()

            logger.info(f"Deleted message: {message_id}")
            return True

        return await rate_limited_call("gmail", _delete)

    @with_error_handling
    async def list_labels(self) -> List[Dict[str, Any]]:
        """List all Gmail labels."""
        async def _list():
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])

            logger.info(f"Found {len(labels)} labels")
            return labels

        cache_k = cache_key("gmail_labels")
        return await rate_limited_call("gmail", cached_call, "gmail", cache_k, _list, ttl=300)

    @with_error_handling
    async def modify_labels(
        self,
        message_id: str,
        add_labels: Optional[List[str]] = None,
        remove_labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Modify message labels."""
        async def _modify():
            body = {}
            if add_labels:
                body['addLabelIds'] = add_labels
            if remove_labels:
                body['removeLabelIds'] = remove_labels

            result = self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body=body
            ).execute()

            logger.info(f"Modified labels for message: {message_id}")
            return result

        return await rate_limited_call("gmail", _modify)
