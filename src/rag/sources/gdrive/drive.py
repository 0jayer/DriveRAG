from __future__ import annotations

from googleapiclient.discovery import build

from rag.sources.data_source import DataSource
from rag.sources.gdrive.cred_provider import CredentialProvider
from rag.sources.gdrive.file_mapper import FileMapper, GDriveFileMapper
from rag.sources.gdrive.path_resolver import PathResolver
from rag.sources.source_file import SourceFile

DEFAULT_FIELDS = (
    "nextPageToken, files(id, name, mimeType, md5Checksum, "
    "modifiedTime, size, parents, trashed)"
)


class Drive(DataSource):
    """Google Drive v3 DataSource implementation."""

    def __init__(
        self,
        credential_provider: CredentialProvider,
        resolver: PathResolver,
        service_builder=build,
        file_mapper: FileMapper | None = None,
        query: str = "trashed = false",
        page_size: int = 1000,
        fields: str = DEFAULT_FIELDS,
        num_retries: int = 5,
    ) -> None:
        self._credential_provider = credential_provider
        self._resolver = resolver
        self._service_builder = service_builder
        self._file_mapper = file_mapper or GDriveFileMapper()
        self._query = query
        self._page_size = page_size
        self._fields = fields
        self._num_retries = num_retries
        self._service = None
        self._account_id: str | None = None

    def connect(self) -> None:
        credentials = self._credential_provider.get_credentials()
        self._service = self._service_builder(
            "drive",
            "v3",
            credentials=credentials,
        )
        self._account_id = (
            self._service.about()
            .get(fields="user(emailAddress)")
            .execute()["user"]["emailAddress"]
        )

    def list_source_files(self) -> list[SourceFile]:
        files = self._resolver.resolve_paths(self._list_raw_files())
        return [
            self.to_source_file(f)
            for f in files
            if not self._resolver.is_folder(f["mimeType"])
        ]

    def fetch_content(self, file) -> bytes:
        raise NotImplementedError("Coming with the parsing step")

    def _list_raw_files(self) -> list[dict]:
        files: list[dict] = []
        page_token = None
        while True:
            results = (
                self._service.files()
                .list(
                    q=self._query,
                    pageSize=self._page_size,
                    fields=self._fields,
                    pageToken=page_token,
                )
                .execute(num_retries=self._num_retries)
            )
            files.extend(results.get("files", []))
            page_token = results.get("nextPageToken")
            if not page_token:
                return files

    def to_source_file(self, raw: dict) -> SourceFile:
        return self._file_mapper.to_source_file(raw, self._account_id)
