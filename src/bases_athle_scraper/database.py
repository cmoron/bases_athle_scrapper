"""
This module contains functions to connect to the PostgreSQL database.
"""

import os
import sqlite3
from urllib.parse import urlparse

from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class SQLiteCursorWrapper:
    """Minimal wrapper translating psycopg2 style placeholders for sqlite."""

    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=None):
        query = query.replace("%s", "?")
        return self.cursor.execute(query, params or [])

    def executemany(self, query, seq_of_params):
        query = query.replace("%s", "?")
        return self.cursor.executemany(query, seq_of_params)

    def __getattr__(self, name):
        return getattr(self.cursor, name)


class SQLiteConnectionWrapper:
    """Return a connection mimicking psycopg2's interface for sqlite."""

    def __init__(self, conn):
        self.conn = conn

    def cursor(self):
        return SQLiteCursorWrapper(self.conn.cursor())

    def __getattr__(self, name):
        return getattr(self.conn, name)


# Load environment variables
load_dotenv()

def get_db_connection(dbname: str | None = None, dsn: str | None = None):
    """Create a connection to the database.

    The connection parameters are resolved in the following order:
    1. ``dsn`` argument or ``DATABASE_URL`` environment variable.
    2. PostgreSQL parameters from environment variables.
    """

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
        # Default to psycopg2 for PostgreSQL style DSN
        return psycopg2.connect(dsn)

    # Fallback to legacy PostgreSQL environment variables
    db_connection = {
        "dbname": dbname or os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "host": "localhost",
        "port": "5432",
    }

    return psycopg2.connect(**db_connection)

def create_database():
    """
    Crée la base de données PostgreSQL si elle n'existe pas.
    """
    dbname = os.getenv('POSTGRES_DB')
    default_dbname = os.getenv('POSTGRES_DEFAULT_DB')

    # Connexion à la base de données par défaut
    conn = get_db_connection(dbname=default_dbname)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Vérifier si la base de données existe déjà
    cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{dbname}'")
    exists = cursor.fetchone()
    if not exists:
        # Créer la base de données
        cursor.execute(f'CREATE DATABASE {dbname}')
        print(f"Base de données '{dbname}' créée avec succès.")
    else:
        print(f"Base de données '{dbname}' existe déjà.")

    cursor.close()
    conn.close()
