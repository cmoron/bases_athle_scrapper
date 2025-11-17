"""
Module pour la gestion du schéma de base de données.
"""
from pathlib import Path
from .db import get_db_connection
from .config import get_logger

logger = get_logger(__name__)

def execute_schema_file(schema_file='schema.sql'):
    """
    Exécute un fichier SQL de schéma.

    Args:
        schema_file: Chemin vers le fichier SQL

    Returns:
        bool: True si succès, False sinon
    """
    schema_path = Path(__file__).parent / schema_file

    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        return False

    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(schema_sql)
            conn.commit()
            logger.info(f"Schema executed successfully from {schema_file}")
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error executing schema: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logger.error(f"Error reading schema file: {e}")
        return False

def create_tables():
    """
    Crée toutes les tables du schéma.
    Utilise le fichier schema.sql.
    """
    logger.info("Creating database tables...")
    return execute_schema_file('schema.sql')

def get_table_stats():
    """
    Récupère les statistiques des tables.

    Returns:
        dict: Statistiques des tables
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    stats = {}

    try:
        # Stats athletes
        cursor.execute("SELECT * FROM v_athletes_stats")
        athlete_stats = cursor.fetchone()
        if athlete_stats:
            stats['athletes'] = {
                'total': athlete_stats[0],
                'with_valid_license': athlete_stats[1],
                'without_license': athlete_stats[2],
                'male': athlete_stats[4],
                'female': athlete_stats[5],
                'oldest_year': athlete_stats[6],
                'youngest_year': athlete_stats[7]
            }

        # Stats clubs
        cursor.execute("SELECT * FROM v_clubs_stats")
        club_stats = cursor.fetchone()
        if club_stats:
            stats['clubs'] = {
                'total': club_stats[0],
                'earliest_year': club_stats[1],
                'latest_year': club_stats[2],
                'avg_years_active': float(club_stats[3]) if club_stats[3] else 0
            }

        return stats

    except Exception as e:
        logger.error(f"Error getting table stats: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    from .config import setup_logging
    setup_logging('db_schema')

    print("Creating database schema...")
    if create_tables():
        print("✓ Schema created successfully")

        print("\nDatabase statistics:")
        stats = get_table_stats()
        if stats:
            if 'athletes' in stats:
                print(f"\nAthletes:")
                for key, value in stats['athletes'].items():
                    print(f"  {key}: {value:,}")
            if 'clubs' in stats:
                print(f"\nClubs:")
                for key, value in stats['clubs'].items():
                    print(f"  {key}: {value}")
        else:
            print("  (No data yet)")
    else:
        print("✗ Failed to create schema")
