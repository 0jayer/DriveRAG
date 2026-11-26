from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from rag.sources.source_file import SourceFile


class FileMapper(ABC):
    """Abstract contract for mapping raw source records into SourceFile objects."""

    @abstractmethod
    def to_source_file(self, raw: dict, account_id: str) -> SourceFile:
        """Convert a raw file metadata dictionary into a SourceFile."""


class GDriveFileMapper(FileMapper):
    """Maps Google Drive v3 API file dictionaries into SourceFile instances."""

    def __init__(self, source_name: str = "gdrive") -> None:
        self._source_name = source_name

    def to_source_file(self, raw: dict, account_id: str) -> SourceFile:
        size = raw.get("size")
        return SourceFile(
            account_id=account_id,
            source=self._source_name,
            external_id=raw["id"],
            name=raw["name"],
            path=raw["path"],
            mime_type=raw["mimeType"],
            source_hash=raw.get("md5Checksum"),
            modified_time=datetime.fromisoformat(
                raw["modifiedTime"].replace("Z", "+00:00")
            ),
            size_bytes=int(size) if size is not None else None,
        )

