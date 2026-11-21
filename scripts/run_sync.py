import os

from dotenv import load_dotenv

from rag.sources.gdrive.drive import Drive
from rag.sources.gdrive.drive_auth_cred_provider import DriveAuth
from rag.sources.gdrive.path_resolver import PathResolver
from rag.storage.database import Database
from rag.storage.postgres_file_repo import PostgresFileRepo


def main() -> None:
    load_dotenv()

    drive = Drive(
        DriveAuth(os.environ["GDRIVE_CREDENTIALS_PATH"], os.environ["GDRIVE_TOKEN_PATH"]),
        PathResolver(),
    ).connect()

    db = Database(os.environ["DATABASE_URL"])
    repo = PostgresFileRepo(db)

    files = drive.list_source_files()
    repo.upsert_files(files)
    print(f"listed {len(files)} files from Drive")

    with db.get_conn() as conn:
        total = conn.execute("SELECT count(*) FROM files").fetchone()[0]
    print(f"files in db: {total}")


if __name__ == "__main__":
    main()