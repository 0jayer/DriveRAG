from rag.sources.gdrive.drive import Drive
from rag.sources.gdrive.drive_auth_cred_provider import DriveAuth
from rag.sources.gdrive.path_resolver import PathResolver

drive = Drive(
    DriveAuth("F:/rag/secrets/credentials.json", "F:/rag/secrets/token.json"),
    PathResolver(),
).connect()

files = drive.list_source_files()

print(f"Total: {len(files)}")
for f in files[:10]:
    print(f.path, "|", f.mime_type)