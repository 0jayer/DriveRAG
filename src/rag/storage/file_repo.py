# src/rag/storage/file_repository.py
from abc import ABC, abstractmethod
from collections.abc import Sequence

from rag.sources.source_file import SourceFile


class FileRepo(ABC):
    @abstractmethod
    def upsert_files(self, files: Sequence[SourceFile]) -> None:
        """Create or update file metadata."""

    @abstractmethod
    def count_files(self) -> int:
        """Return the number of files stored in the repository."""