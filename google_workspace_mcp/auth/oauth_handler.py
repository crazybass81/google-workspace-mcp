"""OAuth 2.0 authentication handler for Google Workspace APIs."""

import os
import pickle
from typing import Optional, List
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from ..utils.logger import setup_logger
from ..utils.error_handler import AuthenticationError

logger = setup_logger(__name__)

# Google Workspace API scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/forms',
    'https://www.googleapis.com/auth/gmail.modify'
]

# Default config directory
DEFAULT_CONFIG_DIR = Path.home() / '.config' / 'gw-mcp'
TOKEN_FILE = 'token.pickle'
CREDENTIALS_FILE = 'credentials.json'


class OAuthHandler:
    """Handles OAuth 2.0 authentication for Google Workspace APIs."""

    def __init__(
        self,
        config_dir: Optional[Path] = None,
        scopes: Optional[List[str]] = None
    ):
        """Initialize OAuth handler.

        Args:
            config_dir: Directory for storing credentials and tokens
            scopes: List of OAuth scopes to request
        """
        self.config_dir = config_dir or DEFAULT_CONFIG_DIR
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.scopes = scopes or SCOPES
        self.credentials: Optional[Credentials] = None

        logger.info(f"OAuth handler initialized with config dir: {self.config_dir}")

    @property
    def token_path(self) -> Path:
        """Get path to token file."""
        return self.config_dir / TOKEN_FILE

    @property
    def credentials_path(self) -> Path:
        """Get path to credentials file."""
        return self.config_dir / CREDENTIALS_FILE

    def load_credentials(self) -> Optional[Credentials]:
        """Load credentials from token file.

        Returns:
            Credentials object if found and valid, None otherwise
        """
        if not self.token_path.exists():
            logger.debug("Token file not found")
            return None

        try:
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
                logger.info("Loaded credentials from token file")
                return creds
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return None

    def save_credentials(self, credentials: Credentials) -> None:
        """Save credentials to token file.

        Args:
            credentials: Credentials to save
        """
        try:
            with open(self.token_path, 'wb') as token:
                pickle.dump(credentials, token)
            logger.info("Saved credentials to token file")
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            raise AuthenticationError(
                "Failed to save authentication credentials",
                original_error=e
            )

    def refresh_credentials(self, credentials: Credentials) -> Credentials:
        """Refresh expired credentials.

        Args:
            credentials: Credentials to refresh

        Returns:
            Refreshed credentials

        Raises:
            AuthenticationError: If refresh fails
        """
        try:
            logger.info("Refreshing expired credentials")
            credentials.refresh(Request())
            self.save_credentials(credentials)
            logger.info("Credentials refreshed successfully")
            return credentials
        except Exception as e:
            logger.error(f"Failed to refresh credentials: {e}")
            raise AuthenticationError(
                "Failed to refresh authentication credentials. "
                "Please re-authenticate.",
                original_error=e
            )

    def authenticate(self, force_reauth: bool = False) -> Credentials:
        """Perform OAuth authentication flow.

        Args:
            force_reauth: Force re-authentication even if credentials exist

        Returns:
            Valid credentials

        Raises:
            AuthenticationError: If authentication fails
        """
        # Load existing credentials
        if not force_reauth:
            creds = self.load_credentials()

            if creds:
                # Check if credentials are valid
                if creds.valid:
                    logger.info("Using existing valid credentials")
                    self.credentials = creds
                    return creds

                # Try to refresh expired credentials
                if creds.expired and creds.refresh_token:
                    try:
                        self.credentials = self.refresh_credentials(creds)
                        return self.credentials
                    except AuthenticationError:
                        logger.warning("Refresh failed, starting new auth flow")

        # Start new authentication flow
        if not self.credentials_path.exists():
            raise AuthenticationError(
                f"Credentials file not found at {self.credentials_path}. "
                f"Please download OAuth 2.0 credentials from Google Cloud Console."
            )

        try:
            logger.info("Starting OAuth authentication flow")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.credentials_path),
                self.scopes
            )
            creds = flow.run_local_server(port=0)
            self.save_credentials(creds)
            self.credentials = creds
            logger.info("Authentication successful")
            return creds

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise AuthenticationError(
                "OAuth authentication failed",
                original_error=e
            )

    def get_service(self, service_name: str, version: str):
        """Get authenticated Google API service.

        Args:
            service_name: Name of the service (e.g., 'drive', 'docs')
            version: API version (e.g., 'v3', 'v1')

        Returns:
            Authenticated service object

        Raises:
            AuthenticationError: If not authenticated
        """
        if not self.credentials:
            logger.info("No credentials, starting authentication")
            self.authenticate()

        try:
            service = build(service_name, version, credentials=self.credentials)
            logger.info(f"Built {service_name} {version} service")
            return service
        except Exception as e:
            logger.error(f"Failed to build service: {e}")
            raise AuthenticationError(
                f"Failed to create {service_name} service",
                original_error=e
            )

    def revoke_credentials(self) -> None:
        """Revoke and delete stored credentials."""
        if self.token_path.exists():
            try:
                self.token_path.unlink()
                logger.info("Credentials revoked and deleted")
            except Exception as e:
                logger.error(f"Failed to delete credentials: {e}")

        self.credentials = None


# Global OAuth handler instance
_oauth_handler: Optional[OAuthHandler] = None


def get_oauth_handler(
    config_dir: Optional[Path] = None,
    scopes: Optional[List[str]] = None
) -> OAuthHandler:
    """Get global OAuth handler instance.

    Args:
        config_dir: Configuration directory
        scopes: OAuth scopes

    Returns:
        OAuthHandler instance
    """
    global _oauth_handler

    if _oauth_handler is None:
        _oauth_handler = OAuthHandler(config_dir=config_dir, scopes=scopes)

    return _oauth_handler
