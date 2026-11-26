from abc import ABC, abstractmethod

from rag.sources.source_file import SourceFile

class DataSource(ABC):
    @abstractmethod
    def connect(self) -> None:
        """Authenticate and get ready to list files."""

    @abstractmethod
    def list_source_files(self) -> list[SourceFile]:
        """Return every file (no folders) with its path resolved."""

    @abstractmethod
    def fetch_content(self, file: SourceFile) -> bytes:
        """Return the file's raw bytes."""