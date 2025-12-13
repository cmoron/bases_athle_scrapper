"""
Core module for Bases Athlé scraper.

Contains:
- db: Database connection management
- config: Logging and configuration
- schema: Database schema management
"""

from .config import cleanup_old_archives, get_logger, setup_logging
from .db import DatabaseConnectionError, get_db_connection
from .schema import create_tables, execute_schema_file, get_table_stats

__all__ = [
    "get_db_connection",
    "DatabaseConnectionError",
    "setup_logging",
    "get_logger",
    "cleanup_old_archives",
    "create_tables",
    "get_table_stats",
    "execute_schema_file",
]
