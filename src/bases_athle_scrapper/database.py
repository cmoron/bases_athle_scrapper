"""Database helpers for storing athletics data."""

from __future__ import annotations

import os
import sqlite3
from typing import Optional
from urllib.parse import urlparse

import psycopg2
from dotenv import load_dotenv
from psycopg2 import OperationalError, sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from .logging_config import get_logger

load_dotenv()
logger = get_logger(__name__)


class DatabaseConnectionError(Exception):
    """Raised when a database connection cannot be established."""


class SQLiteCursorWrapper:
    """Wrap an SQLite cursor to mimic psycopg2 placeholders."""

    def __init__(self, cursor: sqlite3.Cursor) -> None:
        self.cursor = cursor

    def execute(self, query: str, params=None):
        query = query.replace("%s", "?")
        return self.cursor.execute(query, params or [])

    def executemany(self, query: str, seq_of_params):
        query = query.replace("%s", "?")
        return self.cursor.executemany(query, seq_of_params)

    def __getattr__(self, name):  # pragma: no cover - passthrough
        return getattr(self.cursor, name)


class SQLiteConnectionWrapper:
    """Wrap an SQLite connection to align with psycopg2's interface."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def cursor(self):
        return SQLiteCursorWrapper(self.conn.cursor())

    def __getattr__(self, name):  # pragma: no cover - passthrough
        return getattr(self.conn, name)


def get_db_connection(
    dbname: Optional[str] = None, dsn: Optional[str] = None
):  # pragma: no cover - exercised via tests
    """Create a connection to the configured database."""

    dsn = dsn or os.getenv("DATABASE_URL")
    if dsn:
        parsed = urlparse(dsn)
        scheme = parsed.scheme
        if scheme.startswith("sqlite"):
            path = parsed.netloc + parsed.path
            if path in ("", "/", "/:memory:"):
                path = ":memory:"
            conn = sqlite3.connect(path)
            return SQLiteConnectionWrapper(conn)
        return psycopg2.connect(dsn)

    db_connection = {
        "dbname": dbname or os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "host": "localhost",
        "port": "5432",
    }

    missing_params = [k for k, v in db_connection.items() if not v and k != "password"]
    if missing_params:
        error_msg = f"Paramètres de connexion manquants: {', '.join(missing_params)}"
        logger.error(error_msg)
        raise DatabaseConnectionError(error_msg)

    return psycopg2.connect(**db_connection)


def create_database() -> None:
    """Create the configured PostgreSQL database if it does not exist."""

    dbname = os.getenv("POSTGRES_DB")
    default_dbname = os.getenv("POSTGRES_DEFAULT_DB", "postgres")
    if not dbname:
        error_msg = "POSTGRES_DB non défini dans les variables d'environnement"
        logger.error(error_msg)
        raise DatabaseConnectionError(error_msg)

    conn = None
    cursor = None
    try:
        logger.info("Connexion à la base par défaut: %s", default_dbname)
        conn = get_db_connection(dbname=default_dbname)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            (dbname,),
        )
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
            logger.info("Base de données %s créée avec succès.", dbname)
        else:
            logger.info("Base de données %s existe déjà.", dbname)
    except OperationalError as exc:  # pragma: no cover - requires PostgreSQL
        raise DatabaseConnectionError(
            "PostgreSQL n'est pas accessible. Vérifiez que le serveur est démarré."
        ) from exc
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
