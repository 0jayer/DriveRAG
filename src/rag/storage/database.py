from abc import ABC, abstractmethod
from contextlib import AbstractContextManager


class Database(ABC):
    """Abstract contract for a database connection provider.

    Concrete implementations (e.g. PostgresDatabase) live in their own
    modules and are selected via config.yaml.  Code that depends on a
    database connection should type-hint against this class, never against
    a specific backend.
    """

    @abstractmethod
    def get_conn(self) -> AbstractContextManager:
        """Return a context manager that yields a live database connection."""