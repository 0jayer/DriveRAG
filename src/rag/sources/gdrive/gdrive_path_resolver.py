from typing import Final

from rag.sources.gdrive.path_resolver import PathResolver


class GDrivePathResolver(PathResolver):
    """Resolves file paths for the Google Drive v3 API.

    Builds a full folder/file path string (e.g. "Projects/Thesis/draft.pdf")
    from the flat list of file and folder dicts returned by the Drive API.
    """

    FOLDER: Final = "application/vnd.google-apps.folder"

    def is_folder(self, mime_type: str) -> bool:
        return mime_type == self.FOLDER

    def resolve_paths(self, files: list[dict]) -> list[dict]:
        folders = self._build_folder_map(files)
        for f in files:
            f["path"] = self._build_path(f, folders)
        return files

    def _build_folder_map(self, files: list[dict]) -> dict:
        folders: dict = {}
        for f in files:
            if f["mimeType"] == self.FOLDER:
                folders[f["id"]] = (f["name"], (f.get("parents") or [None])[0])
        return folders

    @staticmethod
    def _build_path(file: dict, folders: dict) -> str:
        parts = [file["name"]]
        parent = (file.get("parents") or [None])[0]
        seen: set = set()

        while parent in folders and parent not in seen:
            seen.add(parent)
            name, parent = folders[parent]
            parts.insert(0, name)

        return "/".join(parts)

