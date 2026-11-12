from dataclasses import asdict
from collections.abc import Sequence

from rag.sources.source_file import SourceFile
from rag.storage.database import Database
from rag.storage.file_repo import FileRepo

class PostgresFileRepo(FileRepo):
    UPSERT_FILE_SQL = """
        INSERT INTO files (
            source, account_id, external_id, name, path, mime_type,
            size_bytes, source_hash, modified_time
        ) VALUES (
            %(source)s, %(account_id)s, %(external_id)s, %(name)s, %(path)s,
            %(mime_type)s, %(size_bytes)s, %(source_hash)s, %(modified_time)s
        )
        ON CONFLICT (source, account_id, external_id) DO UPDATE SET
            name = EXCLUDED.name,
            path = EXCLUDED.path,
            mime_type = EXCLUDED.mime_type,
            size_bytes = EXCLUDED.size_bytes,
            source_hash = EXCLUDED.source_hash,
            modified_time = EXCLUDED.modified_time,
            updated_at = now()
        WHERE (
            files.name,
            files.path,
            files.mime_type,
            files.size_bytes,
            files.source_hash,
            files.modified_time
        ) IS DISTINCT FROM (
            EXCLUDED.name,
            EXCLUDED.path,
            EXCLUDED.mime_type,
            EXCLUDED.size_bytes,
            EXCLUDED.source_hash,
            EXCLUDED.modified_time
        )
    """
    def __init__(self, database:Database) -> None:
        self._database = database

    def upsert_files(self, files: Sequence[SourceFile]) -> None:
        if not files:
            return
        with self._database.get_conn() as conn:
            with conn.cursor() as cur:
                cur.executemany(self.UPSERT_FILE_SQL, [asdict(f) for f in files])
