from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from rag.sources.gdrive.cred_provider import CredentialProvider
from rag.sources.gdrive.drive import Drive
from rag.sources.gdrive.drive_auth_cred_provider import DriveAuth
from rag.sources.gdrive.file_mapper import FileMapper, GDriveFileMapper
from rag.sources.gdrive.gdrive_path_resolver import GDrivePathResolver
from rag.sources.gdrive.token_store import JsonTokenStore, TokenStore
from rag.sources.source_file import SourceFile


class FakeTokenStore(TokenStore):
    def __init__(self, creds=None) -> None:
        self.creds = creds
        self.loaded_scopes: list[list[str]] = []
        self.saved: list[object] = []

    def load(self, scopes):
        self.loaded_scopes.append(list(scopes))
        return self.creds

    def save(self, creds) -> None:
        self.saved.append(creds)
        self.creds = creds


def test_json_token_store_rejects_empty_path() -> None:
    with pytest.raises(ValueError, match="token path is required"):
        JsonTokenStore("")


def test_json_token_store_handles_missing_and_corrupt_files(tmp_path) -> None:
    token_file = tmp_path / "token.json"
    store = JsonTokenStore(str(token_file))

    assert store.load(["scope.a"]) is None

    token_file.write_text("{not valid json", encoding="utf-8")
    assert store.load(["scope.a"]) is None


def test_json_token_store_checks_required_scopes(tmp_path) -> None:
    token_file = tmp_path / "token.json"
    token_file.write_text('{"scopes": ["scope.a"]}', encoding="utf-8")
    store = JsonTokenStore(str(token_file))

    assert store.load(["scope.a", "scope.b"]) is None


def test_drive_auth_uses_injected_token_store_and_custom_scopes() -> None:
    fake_creds = SimpleNamespace(expired=False, refresh_token=None, valid=True)
    store = FakeTokenStore(creds=fake_creds)

    auth = DriveAuth(
        credentials_path="credentials.json",
        scopes=["https://www.googleapis.com/auth/drive.metadata.readonly"],
        token_store=store,
    )

    assert auth.get_credentials() is fake_creds
    assert store.loaded_scopes == [
        ["https://www.googleapis.com/auth/drive.metadata.readonly"]
    ]


def test_drive_auth_requires_tokens_path_when_using_default_store() -> None:
    with pytest.raises(ValueError, match="token path is required"):
        DriveAuth(credentials_path="credentials.json")


def test_gdrive_file_mapper_maps_raw_dict() -> None:
    mapper = GDriveFileMapper(source_name="custom-drive")
    raw = {
        "id": "file-1",
        "name": "notes.md",
        "path": "Docs/notes.md",
        "mimeType": "text/markdown",
        "md5Checksum": "abc123",
        "modifiedTime": "2026-01-02T03:04:05Z",
        "size": "42",
    }

    result = mapper.to_source_file(raw, account_id="user@example.com")

    assert result == SourceFile(
        account_id="user@example.com",
        source="custom-drive",
        external_id="file-1",
        name="notes.md",
        path="Docs/notes.md",
        mime_type="text/markdown",
        source_hash="abc123",
        modified_time=datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
        size_bytes=42,
    )


def test_drive_respects_custom_query_options_and_file_mapper() -> None:
    class StubCreds(CredentialProvider):
        def get_credentials(self):
            return object()

    class CustomMapper(FileMapper):
        def to_source_file(self, raw: dict, account_id: str) -> SourceFile:
            return SourceFile(
                account_id=account_id,
                source="mapped",
                external_id=raw["id"],
                name=raw["name"],
                path=raw["path"],
                mime_type=raw["mimeType"],
                source_hash=None,
                modified_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
                size_bytes=None,
            )

    recorded_list_calls: list[dict] = []
    recorded_retries: list[int] = []

    class FakeFilesResource:
        def list(self, **kwargs):
            recorded_list_calls.append(kwargs)
            return self

        def execute(self, num_retries=0):
            recorded_retries.append(num_retries)
            return {
                "files": [
                    {
                        "id": "f1",
                        "name": "doc.pdf",
                        "mimeType": "application/pdf",
                        "parents": [],
                    }
                ]
            }

    class FakeAboutResource:
        def get(self, fields):
            return self

        def execute(self):
            return {"user": {"emailAddress": "owner@example.com"}}

    class FakeService:
        def files(self):
            return FakeFilesResource()

        def about(self):
            return FakeAboutResource()

    drive = Drive(
        credential_provider=StubCreds(),
        resolver=GDrivePathResolver(),
        service_builder=lambda *args, **kwargs: FakeService(),
        file_mapper=CustomMapper(),
        query="mimeType = 'application/pdf'",
        page_size=250,
        fields="nextPageToken, files(id, name, mimeType, parents)",
        num_retries=2,
    )
    drive.connect()
    files = drive.list_source_files()

    assert recorded_list_calls == [
        {
            "q": "mimeType = 'application/pdf'",
            "pageSize": 250,
            "fields": "nextPageToken, files(id, name, mimeType, parents)",
            "pageToken": None,
        }
    ]
    assert recorded_retries == [2]
    assert len(files) == 1
    assert files[0].source == "mapped"
    assert files[0].account_id == "owner@example.com"


def test_gdrive_path_resolver_uses_is_folder_hook() -> None:
    class CustomFolderResolver(GDrivePathResolver):
        def is_folder(self, mime_type: str) -> bool:
            return mime_type in {self.FOLDER, "application/x-custom-folder"}

    files = [
        {"id": "1", "name": "Custom", "mimeType": "application/x-custom-folder"},
        {
            "id": "2",
            "name": "report.txt",
            "mimeType": "text/plain",
            "parents": ["1"],
        },
    ]

    CustomFolderResolver().resolve_paths(files)
    assert files[1]["path"] == "Custom/report.txt"

