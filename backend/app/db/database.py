"""
DuckDB Database Manager for ContagionGraph.
Handles initialization, connection pooling, and parquet views.
"""
from pathlib import Path
from typing import Optional
import duckdb

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "contagion.duckdb"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


class DatabaseManager:
    def __init__(self, db_path: Optional[str | Path] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.db_path))

    def _init_schema(self):
        with duckdb.connect(str(self.db_path)) as con:
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            con.execute(schema_sql)

    def execute(self, query: str, params: Optional[tuple | list] = None):
        with duckdb.connect(str(self.db_path)) as con:
            if params:
                return con.execute(query, params).fetchall()
            return con.execute(query).fetchall()

    def query_df(self, query: str, params: Optional[tuple | list] = None):
        with duckdb.connect(str(self.db_path)) as con:
            if params:
                return con.execute(query, params).df()
            return con.execute(query).df()


# Global default instance
db_manager = DatabaseManager()
