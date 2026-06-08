"""SQLite + SQLCipher database service."""

import sqlite3
from pathlib import Path

from app.config import settings


class DatabaseService:
    """Manage encrypted SQLite database connection."""

    def __init__(self, db_path: str | None = None, encryption_key: str | None = None):
        self.db_path = db_path or settings.db_path
        self.encryption_key = encryption_key or settings.db_encryption_key
        self._connection: sqlite3.Connection | None = None

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection (SQLCipher if key provided, plain SQLite otherwise)."""
        if self._connection is not None:
            return self._connection

        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            import sqlcipher3
            self._connection = sqlcipher3.connect(self.db_path)
            if self.encryption_key:
                self._connection.execute(f"PRAGMA key = '{self.encryption_key}'")
        except ImportError:
            self._connection = sqlite3.connect(self.db_path)

        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection

    def initialize_schema(self) -> None:
        """Create database tables if they don't exist."""
        schema_path = Path(__file__).resolve().parent.parent / "db" / "schema.sql"
        with open(schema_path, encoding="utf-8") as f:
            schema_sql = f.read()

        conn = self.get_connection()
        conn.executescript(schema_sql)
        conn.commit()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a single SQL statement."""
        conn = self.get_connection()
        return conn.execute(query, params)

    def execute_many(self, query: str, params_list: list[tuple]) -> sqlite3.Cursor:
        """Execute a SQL statement with multiple parameter sets."""
        conn = self.get_connection()
        return conn.executemany(query, params_list)

    def fetch_one(self, query: str, params: tuple = ()) -> sqlite3.Row | None:
        """Fetch a single row."""
        conn = self.get_connection()
        cursor = conn.execute(query, params)
        return cursor.fetchone()

    def fetch_all(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Fetch all rows."""
        conn = self.get_connection()
        cursor = conn.execute(query, params)
        return cursor.fetchall()

    def commit(self) -> None:
        """Commit current transaction."""
        if self._connection:
            self._connection.commit()

    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None


db_service = DatabaseService()
