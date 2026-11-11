import os
from pathlib import Path
import psycopg
from dataclasses import asdict
from dotenv import load_dotenv
from .source_file import SourceFile

load_dotenv()

# DB_NAME = os.getenv("POSTGRES_DB")
# DB_USER = os.getenv("POSTGRES_USER")

DB_URL = os.getenv("DATABASE_URL")
# print(DB_NAME)
# print(DB_URL)
UPSERT_FILE_SQL = """
INSERT INTO files (
    account_id, external_id, source, name, path, mime_type,
    size_bytes, source_hash, modified_time
) VALUES (
    %(account_id)s, %(external_id)s, %(source)s, %(name)s, %(path)s, %(mime_type)s,
    %(size_bytes)s, %(source_hash)s, %(modified_time)s
)
ON CONFLICT (account_id, external_id) DO UPDATE SET
    name      = EXCLUDED.name,
    path      = EXCLUDED.path,
    mime_type = EXCLUDED.mime_type,
    updated_at = now()
WHERE (files.name, files.path, files.mime_type)
      IS DISTINCT FROM (EXCLUDED.name, EXCLUDED.path, EXCLUDED.mime_type)
"""


def init_db(conn):
    sql_path = Path(__file__).parents[1] / "sql" / "schema.sql"
    with open(sql_path, "r", encoding="utf-8") as sql_file:
        sql_script = sql_file.read()
    #print(sql_script)
    conn.execute(sql_script)

def get_conn():
    if not DB_URL:
        raise RuntimeError("DATABASE_URL is not set (check your .env)")
    return psycopg.connect(DB_URL)

def upsert_files(conn, files: list[SourceFile]) -> None:
    if not files:
        return
    with conn.cursor() as cur:
        cur.executemany(UPSERT_FILE_SQL, [asdict(f) for f in files])

if __name__ == "__main__":
    with get_conn() as conn:
        init_db(conn)
        # print(conn.execute("SELECT count(*) FROM files").fetchone())
        # print(conn.execute("SELECT to_regclass('public.files'), to_regclass('public.chunks')").fetchone())