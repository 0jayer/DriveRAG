
from typing import Final

class PathResolver: 
    FOLDER: Final = "application/vnd.google-apps.folder"

    #building folder map, e.g getting folder name from their id
    def _build_folder_map(self,files):
        folders = {}
        for f in files:
            if f["mimeType"] == self.FOLDER:
                folders[f["id"]] = (f["name"], (f.get("parents") or [None])[0])

        return folders

    #building folder paths
    @staticmethod 
    def _build_path(file, folders):
        parts = [file["name"]]
        parent = (file.get("parents") or [None])[0]
        seen = set()

        #finding parent folders if they havent already been found and making a file path
        while parent in folders and parent not in seen:
            seen.add(parent)
            name,parent = folders[parent]
            parts.insert(0, name)

        return "/".join(parts)

    #appending folder path in to the files
    def resolve_paths(self,files):
        folders = self._build_folder_map(files)
        for f in files:
            f["path"] = self._build_path(f,folders)
        return files