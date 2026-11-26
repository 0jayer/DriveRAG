from __future__ import annotations

from collections.abc import Sequence

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from rag.sources.gdrive.cred_provider import CredentialProvider
from rag.sources.gdrive.token_store import JsonTokenStore, TokenStore


class DriveAuth(CredentialProvider):
    """Obtains and refreshes Google Drive OAuth2 credentials."""

    SCOPES = [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid",
    ]

    def __init__(
        self,
        credentials_path: str,
        tokens_path: str | None = None,
        port: int = 8000,
        scopes: Sequence[str] | None = None,
        token_store: TokenStore | None = None,
    ) -> None:
        if not credentials_path:
            raise ValueError("Google Drive credentials path is required")
        if token_store is None:
            if not tokens_path:
                raise ValueError("Google Drive token path is required")
            token_store = JsonTokenStore(tokens_path)

        self.credentials_path = credentials_path
        self.tokens_path = tokens_path
        self.port = port
        self._scopes = list(scopes) if scopes is not None else list(self.SCOPES)
        self._token_store = token_store

    def get_credentials(self) -> Credentials:
        creds = self._token_store.load(self._scopes)

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._token_store.save(creds)
            except RefreshError:
                creds = None

        if not creds or not creds.valid:
            creds = self._login()

        return creds

    def _login(self) -> Credentials:
        flow = InstalledAppFlow.from_client_secrets_file(
            self.credentials_path, self._scopes
        )
        creds = flow.run_local_server(port=self.port)
        self._token_store.save(creds)
        return creds
