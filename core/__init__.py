"""
Core module for Bases Athlé scraper.

Contains:
- db: Database connection management
- config: Logging and configuration
- schema: Database schema management
"""

from .db import get_db_connection, DatabaseConnectionError
from .config import setup_logging, get_logger, cleanup_old_archives
from .schema import create_tables, get_table_stats, execute_schema_file

__all__ = [
    'get_db_connection',
    'DatabaseConnectionError',
    'setup_logging',
    'get_logger',
    'cleanup_old_archives',
    'create_tables',
    'get_table_stats',
    'execute_schema_file',
]
