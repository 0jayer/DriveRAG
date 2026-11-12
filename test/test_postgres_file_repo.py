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


def test_upsert_files_inserts_and_updates_a_file(database: Database) -> None:
    repository = PostgresFileRepo(database)
    external_id = f"pytest-{uuid4()}"

    original = SourceFile(
        source="test-source",
        account_id="test-account",
        external_id=external_id,
        name="original.md",
        path="docs/original.md",
        mime_type="text/markdown",
        size_bytes=10,
        source_hash="original-hash",
        modified_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    updated = SourceFile(
        source=original.source,
        account_id=original.account_id,
        external_id=original.external_id,
        name="updated.md",
        path="docs/updated.md",
        mime_type="text/markdown",
        size_bytes=20,
        source_hash="updated-hash",
        modified_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    try:
        repository.upsert_files([original])
        repository.upsert_files([updated])

        with database.get_conn() as connection:
            row = connection.execute(
                """
                SELECT name, path, size_bytes, source_hash, modified_time
                FROM files
                WHERE source = %s AND account_id = %s AND external_id = %s
                """,
                (updated.source, updated.account_id, updated.external_id),
            ).fetchone()

        assert row == (
            "updated.md",
            "docs/updated.md",
            20,
            "updated-hash",
            datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
    finally:
        with database.get_conn() as connection:
            connection.execute(
                """
                DELETE FROM files
                WHERE source = %s AND account_id = %s AND external_id = %s
                """,
                (original.source, original.account_id, original.external_id),
            )
