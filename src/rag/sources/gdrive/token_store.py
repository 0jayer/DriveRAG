from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from collections.abc import Sequence

from google.oauth2.credentials import Credentials


class TokenStore(ABC):
    """Abstract contract for loading and persisting OAuth credentials."""

    @abstractmethod
    def load(self, scopes: Sequence[str]) -> Credentials | None:
        """Return stored credentials if present and valid for the requested scopes."""

    @abstractmethod
    def save(self, creds: Credentials) -> None:
        """Persist credentials for future reuse."""


class JsonTokenStore(TokenStore):
    """Stores Google OAuth2 user credentials in a local JSON file."""

    def __init__(self, tokens_path: str) -> None:
        if not tokens_path:
            raise ValueError("Google Drive token path is required")
        self._tokens_path = tokens_path

    def load(self, scopes: Sequence[str]) -> Credentials | None:
        if not os.path.exists(self._tokens_path) or not self._has_scopes(scopes):
            return None
        return Credentials.from_authorized_user_file(self._tokens_path, list(scopes))

    def save(self, creds: Credentials) -> None:
        with open(self._tokens_path, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    def _has_scopes(self, required_scopes: Sequence[str]) -> bool:
        try:
            with open(self._tokens_path, encoding="utf-8") as file:
                granted = set(json.load(file).get("scopes", []))
        except json.JSONDecodeError:
            return False
        return set(required_scopes) <= granted

