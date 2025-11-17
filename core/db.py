"""
This module contains functions to connect to the PostgreSQL database.
"""
import os
import sqlite3
from typing import Optional
from urllib.parse import urlparse
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2 import OperationalError, sql
from .config import get_logger

logger = get_logger(__name__)
load_dotenv()

class DatabaseConnectionError(Exception):
    """Exception levée lors d'un échec de connexion à la base de données."""

class SQLiteCursorWrapper:
    """Minimal wrapper translating psycopg2 style placeholders for sqlite."""

    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=None):
        """Translate %s placeholders to ? for sqlite."""
        query = query.replace("%s", "?")
        return self.cursor.execute(query, params or [])

    def executemany(self, query, seq_of_params):
        """Translate %s placeholders to ? for sqlite."""
        query = query.replace("%s", "?")
        return self.cursor.executemany(query, seq_of_params)

    def __getattr__(self, name):
        return getattr(self.cursor, name)


class SQLiteConnectionWrapper:
    """Return a connection mimicking psycopg2's interface for sqlite."""

    def __init__(self, conn):
        self.conn = conn

    def cursor(self):
        """ Mimic psycopg2's cursor method. """
        return SQLiteCursorWrapper(self.conn.cursor())

    def __getattr__(self, name):
        return getattr(self.conn, name)


def get_db_connection(dbname: Optional[str] = None, dsn: Optional[str] = None):
    """Create a connection to the database.

    The connection parameters are resolved in the following order:
    1. ``dsn`` argument or ``DATABASE_URL`` environment variable.
    2. PostgreSQL parameters from environment variables.

    Args:
        dbname: Nom de la base de données (optionnel)
        dsn: Data Source Name pour la connexion (optionnel)

    Returns:
        Connection object (SQLiteConnectionWrapper ou psycopg2.connection)

    Raises:
        DatabaseConnectionError: Si la connexion échoue
        sqlite3.Error: Pour les erreurs SQLite spécifiques
        psycopg2.OperationalError: Pour les erreurs de connexion PostgreSQL
    """
    dsn = dsn or os.getenv("DATABASE_URL")

    # Connexion via DSN
    if dsn:
        parsed = urlparse(dsn)
        scheme = parsed.scheme

        if scheme.startswith("sqlite"):
            path = parsed.netloc + parsed.path
            if path in ("", "/", "/:memory:"):
                path = ":memory:"

            conn = sqlite3.connect(path)
            return SQLiteConnectionWrapper(conn)

        # PostgreSQL via DSN
        return psycopg2.connect(dsn)

    # Connexion PostgreSQL via variables d'environnement
    db_connection = {
        "dbname": dbname or os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "host": "localhost",
        "port": "5432",
    }

    # Validation des paramètres requis
    missing_params = [k for k, v in db_connection.items() if not v and k != "password"]
    if missing_params:
        error_msg = f"Paramètres de connexion manquants: {', '.join(missing_params)}"
        logger.error(error_msg)
        raise DatabaseConnectionError(error_msg)

    return psycopg2.connect(**db_connection)


def create_database():
    """
    Crée la base de données PostgreSQL si elle n'existe pas.

    Raises:
        DatabaseConnectionError: Si la connexion échoue
        psycopg2.DatabaseError: Si la création de la base échoue
    """
    dbname = os.getenv('POSTGRES_DB')
    default_dbname = os.getenv('POSTGRES_DEFAULT_DB', 'postgres')

    if not dbname:
        error_msg = "POSTGRES_DB non défini dans les variables d'environnement"
        logger.error(error_msg)
        raise DatabaseConnectionError(error_msg)

    conn = None
    cursor = None

    try:
        # Connexion à la base de données par défaut
        logger.info("Connexion à la base par défaut: %s", default_dbname)
        conn = get_db_connection(dbname=default_dbname)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Vérifier si la base de données existe déjà
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            (dbname,)
        )
        exists = cursor.fetchone()

        if not exists:
            # Créer la base de données (utilisation d'identifiant sécurisé)
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname))
            )
            logger.info("Base de données %s créée avec succès.", dbname)
        else:
            logger.info("Base de données %s existe déjà.", dbname)

    except OperationalError as e:
        raise DatabaseConnectionError(
            "PostgreSQL n'est pas accessible. Vérifiez que le serveur est démarré."
        ) from e

    finally:
        # Fermeture propre des ressources
        if cursor:
            cursor.close()
        if conn:
            conn.close()
