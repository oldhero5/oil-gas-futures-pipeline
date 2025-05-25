#!/usr/bin/env python3
"""Initialize DuckDB database schema for oil & gas futures analysis."""

import sys
from pathlib import Path

import duckdb
from structlog import get_logger

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.storage.schemas import create_all_tables

logger = get_logger()


def setup_database(db_path: str = "data/futures_analysis.db") -> None:
    """Initialize database with all required tables."""
    # Ensure data directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    logger.info("Initializing database", db_path=db_path)

    try:
        conn = duckdb.connect(db_path)
        create_all_tables(conn)

        # Verify tables were created
        tables = conn.execute("SHOW TABLES").fetchall()
        logger.info("Database initialized successfully", tables=tables)

        conn.close()
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


if __name__ == "__main__":
    setup_database()
