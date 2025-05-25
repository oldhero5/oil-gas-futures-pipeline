"""Database connection manager for DuckDB."""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import duckdb
from structlog import get_logger

logger = get_logger()


class DatabaseManager:
    """Manage DuckDB database connections."""

    def __init__(self, db_path: str = "data/futures_analysis.db") -> None:
        """Initialize database manager.

        Args:
            db_path: Path to the DuckDB database file
        """
        self.db_path = db_path
        # Ensure the directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """Get a database connection as a context manager.

        Yields:
            DuckDB connection object
        """
        conn = None
        try:
            conn = duckdb.connect(self.db_path)
            logger.debug("Opened database connection", db_path=self.db_path)
            yield conn
        except Exception as e:
            logger.error("Database error", error=str(e))
            raise
        finally:
            if conn:
                conn.close()
                logger.debug("Closed database connection")

    def execute_query(self, query: str, params: list = None) -> duckdb.DuckDBPyRelation:
        """Execute a query and return the result.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            Query result
        """
        with self.get_connection() as conn:
            if params:
                return conn.execute(query, params)
            return conn.execute(query)

    def health_check(self) -> bool:
        """Check if the database is accessible and has the expected schema.

        Returns:
            True if database is healthy
        """
        try:
            with self.get_connection() as conn:
                # Check if key tables exist
                tables = conn.execute("SHOW TABLES").fetchall()
                table_names = [t[0] for t in tables]

                expected_tables = [
                    "commodities",
                    "futures_contracts",
                    "futures_prices",
                    "options_contracts",
                    "options_prices",
                    "implied_volatility",
                    "greeks",
                ]

                missing_tables = [t for t in expected_tables if t not in table_names]

                if missing_tables:
                    logger.warning("Missing database tables", missing=missing_tables)
                    return False

                logger.info("Database health check passed")
                return True

        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False
