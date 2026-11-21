import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
import psycopg
from dotenv import load_dotenv

from rag.sources.source_file import SourceFile
from rag.storage.database import Database
from rag.storage.postgres_file_repo import PostgresFileRepo
from rag.storage.schema_initializer import SchemaInitializer


load_dotenv()
pytestmark = pytest.mark.integration


@pytest.fixture
def database() -> Database:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not set")

    database = Database(database_url)
    try:
        SchemaInitializer(database).init_db()
    except psycopg.OperationalError:
        pytest.skip("PostgreSQL is not running")

    return database


def make_file(external_id: str, account_id: str = "test-account", **kw) -> SourceFile:
    return SourceFile(
        source="test-source",
        account_id=account_id,
        external_id=external_id,
        name=kw.get("name", "a.md"),
        path=kw.get("path", "docs/a.md"),
        mime_type="text/markdown",
        size_bytes=kw.get("size_bytes", 10),
        source_hash=kw.get("source_hash", "h"),
        modified_time=kw.get("modified_time", datetime(2026, 1, 1, tzinfo=timezone.utc)),
    )


@pytest.fixture
def cleanup(database):
    prefix = f"pytest-{uuid4()}"
    yield prefix
    with database.get_conn() as conn:
        conn.execute("DELETE FROM files WHERE external_id LIKE %s", (prefix + "%",))


def fetch(database, f: SourceFile, columns: str):
    with database.get_conn() as conn:
        return conn.execute(
            f"SELECT {columns} FROM files "
            "WHERE source = %s AND account_id = %s AND external_id = %s",
            (f.source, f.account_id, f.external_id),
        ).fetchone()


def count(database, prefix) -> int:
    with database.get_conn() as conn:
        return conn.execute(
            "SELECT count(*) FROM files WHERE external_id LIKE %s", (prefix + "%",)
        ).fetchone()[0]


def test_upsert_inserts_a_new_file(database, cleanup):
    f = make_file(f"{cleanup}-a", name="a.md", path="docs/a.md", size_bytes=10, source_hash="h1")
    PostgresFileRepo(database).upsert_files([f])

    assert fetch(database, f, "name, path, size_bytes, source_hash, modified_time") == (
        "a.md", "docs/a.md", 10, "h1", f.modified_time,
    )


def test_upsert_updates_metadata_of_an_existing_file(database, cleanup):
    repo = PostgresFileRepo(database)
    original = make_file(f"{cleanup}-a")
    updated = make_file(
        f"{cleanup}-a", name="b.md", path="docs/b.md", size_bytes=20, source_hash="h2",
        modified_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )
    repo.upsert_files([original])
    repo.upsert_files([updated])

    assert fetch(database, updated, "name, path, size_bytes, source_hash, modified_time") == (
        "b.md", "docs/b.md", 20, "h2", updated.modified_time,
    )


def test_upsert_of_unchanged_file_does_not_touch_updated_at(database, cleanup):
    repo = PostgresFileRepo(database)
    f = make_file(f"{cleanup}-a")
    repo.upsert_files([f])
    before = fetch(database, f, "updated_at")
    repo.upsert_files([f])
    assert fetch(database, f, "updated_at") == before


def test_upsert_does_not_reset_status(database, cleanup):
    repo = PostgresFileRepo(database)
    f = make_file(f"{cleanup}-a")
    repo.upsert_files([f])
    with database.get_conn() as conn:
        conn.execute(
            "UPDATE files SET status = 'ok' WHERE external_id = %s", (f.external_id,)
        )
    repo.upsert_files([make_file(f"{cleanup}-a", name="changed.md", source_hash="h2")])
    assert fetch(database, f, "status") == ("ok",)


def test_upsert_is_idempotent(database, cleanup):
    repo = PostgresFileRepo(database)
    files = [make_file(f"{cleanup}-{i}") for i in range(3)]
    repo.upsert_files(files)
    repo.upsert_files(files)
    assert count(database, cleanup) == 3


def test_upsert_empty_list_is_a_noop(database):
    PostgresFileRepo(database).upsert_files([])


def test_same_external_id_in_different_accounts_are_separate_rows(database, cleanup):
    PostgresFileRepo(database).upsert_files([
        make_file(f"{cleanup}-x", account_id="acct-1"),
        make_file(f"{cleanup}-x", account_id="acct-2"),
    ])
    assert count(database, cleanup) == 2