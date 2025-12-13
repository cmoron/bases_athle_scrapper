"""
Fixtures pytest pour les tests avec PostgreSQL via testcontainers.
"""

import os
import sys
from pathlib import Path

import pytest
from testcontainers.postgres import PostgresContainer

# Ajouter le répertoire racine au path pour les imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def postgres_container():
    """
    Lance un conteneur PostgreSQL temporaire pour toute la session de tests.
    Le conteneur est automatiquement détruit à la fin des tests.
    """
    with PostgresContainer("postgres:16", driver="psycopg2") as postgres:
        # Récupérer le DSN de connexion et convertir au format psycopg2
        # testcontainers retourne "postgresql+psycopg2://..." mais psycopg2 attend "postgresql://..."
        dsn = postgres.get_connection_url().replace("postgresql+psycopg2://", "postgresql://")
        yield dsn


@pytest.fixture(scope="session")
def postgres_schema(postgres_container):
    """
    Crée le schéma complet de la base de données dans le conteneur PostgreSQL.
    Cette fixture dépend de postgres_container et n'est exécutée qu'une fois par session.
    """
    from core.db import get_db_connection
    from core.schema import create_tables

    # Configurer la variable d'environnement pour que get_db_connection() utilise le conteneur
    os.environ["DATABASE_URL"] = postgres_container

    # Créer les tables, index, fonctions et triggers
    create_tables()

    yield postgres_container


@pytest.fixture
def db_dsn(postgres_schema, monkeypatch):
    """
    Fixture pour chaque test : fournit le DSN et nettoie les données entre les tests.

    Cette fixture:
    - Dépend de postgres_schema (donc le schéma est créé une fois)
    - Configure DATABASE_URL pour le test
    - Nettoie toutes les données après chaque test (TRUNCATE)
    - Garde le schéma intact pour les tests suivants
    """
    from core.db import get_db_connection

    # Configurer l'environnement pour ce test
    monkeypatch.setenv("DATABASE_URL", postgres_schema)

    yield postgres_schema

    # Nettoyage : vider les tables pour le prochain test
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # TRUNCATE CASCADE vide toutes les tables tout en gardant le schéma
        cursor.execute("TRUNCATE TABLE athletes, clubs RESTART IDENTITY CASCADE")
        conn.commit()
    except Exception as e:
        print(f"Warning: Failed to clean database: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
