"""
This module contains functions to connect to the database
"""

import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Load environment variables
load_dotenv()

def get_db_connection(dbname=None):
    """
    Create a connection to the database

    Returns:
        psycopg2.connection: Connection to the database
    """
    db_connection = {
        'dbname': dbname or os.getenv('POSTGRES_DB'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'host': 'localhost',
        'port': '5432'
    }

    conn = psycopg2.connect(**db_connection)
    return conn

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
