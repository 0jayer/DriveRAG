from rag.drive.drive import Drive
from rag.drive.drive_auth import DriveAuth
from rag.drive.path_resolver import PathResolver

drive = Drive(
    DriveAuth("F:/rag/secrets/credentials.json", "F:/rag/secrets/token.json"),
    PathResolver(),
).connect()

files = drive.list_source_files()

print(f"Total: {len(files)}")
for f in files[:10]:
    print(f.path, "|", f.mime_type)