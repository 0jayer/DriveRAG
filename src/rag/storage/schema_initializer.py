from importlib.resources import files

from rag.storage.database import Database


class SchemaInitializer:
    def __init__(self, database: Database) -> None:
        self._database = database

    def init_db(self) -> None:
        schema_path = (
            files("rag.storage")
            .joinpath("schema.sql")
            .read_text(encoding="utf-8")
        )

        with self._database.get_conn() as connection:
            connection.execute(schema_path)