from contextlib import contextmanager
from collections.abc import Generator

import psycopg

class Database:
    def __init__(self, db_url: str) -> None:
        if not db_url:
            raise ValueError("Database URL is required")
        
        self._db_url = db_url

    #A context manager for database connnection, safer way to manage database
    @contextmanager
    def get_conn(self) -> Generator[psycopg.Connection, None, None]:
        with psycopg.connect(self._db_url) as connection:
            yield connection