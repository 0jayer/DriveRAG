from abc import ABC, abstractmethod


class PathResolver(ABC):
    """Abstract contract for resolving folder paths within a data source.

    Concrete implementations live in their own modules (e.g.
    GDrivePathResolver) and are selected via config.yaml.  Code that
    depends on path resolution should type-hint against this class only.
    """

    @abstractmethod
    def resolve_paths(self, files: list[dict]) -> list[dict]:
        """Annotate each file dict with a 'path' key built from folder
        ancestry, and return the same list."""

    @abstractmethod
    def is_folder(self, mime_type: str) -> bool:
        """Return True if the given MIME type represents a folder/container
        that should be excluded from the file listing."""