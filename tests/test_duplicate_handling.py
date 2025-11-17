"""
Tests for duplicate athlete handling based on license_id
"""
import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.db import get_db_connection
from scraper.list_athletes import store_athletes


def create_test_schema(conn):
    """Create a simplified schema for SQLite tests"""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS athletes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ffa_id TEXT NOT NULL UNIQUE,
            license_id TEXT,
            name TEXT NOT NULL,
            normalized_name TEXT NOT NULL,
            url TEXT,
            birth_date TEXT,
            sexe TEXT,
            nationality TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()


@pytest.fixture
def db_dsn(tmp_path, monkeypatch):
    """Setup test database"""
    db_file = tmp_path / "test.db"
    dsn = f"sqlite:///{db_file}"
    monkeypatch.setenv("DATABASE_URL", dsn)

    # Create test schema
    conn = get_db_connection()
    create_test_schema(conn)
    conn.close()

    yield dsn

    if db_file.exists():
        db_file.unlink()


def test_store_new_athlete(db_dsn):
    """Test storing a new athlete"""
    athletes = {
        "123": {
            "name": "Test Athlete",
            "url": "http://example.com/123",
            "birth_date": "2000",
            "license_id": "L123",
            "sexe": "M",
            "nationality": "FRA",
        }
    }

    store_athletes(athletes)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT ffa_id, name, license_id FROM athletes WHERE ffa_id = ?", ("123",))
    row = cur.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "123"
    assert row[1] == "Test Athlete"
    assert row[2] == "L123"


def test_update_existing_athlete_same_id(db_dsn):
    """Test updating an athlete with the same ffa_id"""
    # Insert initial athlete
    athletes = {
        "123": {
            "name": "Old Name",
            "url": "http://old.com/123",
            "birth_date": "2000",
            "license_id": "L123",
            "sexe": "M",
            "nationality": "FRA",
        }
    }
    store_athletes(athletes)

    # Update with new data
    athletes = {
        "123": {
            "name": "New Name",
            "url": "http://new.com/123",
            "birth_date": "2000",
            "license_id": "L123",
            "sexe": "M",
            "nationality": "FRA",
        }
    }
    store_athletes(athletes)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, url FROM athletes WHERE ffa_id = ?", ("123",))
    row = cur.fetchone()
    conn.close()

    assert row[0] == "New Name"
    assert row[1] == "http://new.com/123"


def test_different_ffa_ids_same_license(db_dsn):
    """Test that two different ffa_ids can have the same license_id"""
    # With the new schema, ffa_id is the unique key, not license_id
    # So two different ffa_ids with same license_id should both be stored

    # Insert athlete with first ffa_id
    athletes = {
        "OLD123": {
            "name": "Test Athlete",
            "url": "http://bases.athle.fr/OLD123",
            "birth_date": "2000",
            "license_id": "L123",
            "sexe": "M",
            "nationality": "FRA",
        }
    }
    store_athletes(athletes)

    # Insert same athlete with different ffa_id (same license_id)
    athletes = {
        "NEW456": {
            "name": "Test Athlete",
            "url": "http://www.athle.fr/athletes/NEW456",
            "birth_date": "2000",
            "license_id": "L123",
            "sexe": "M",
            "nationality": "FRA",
        }
    }
    store_athletes(athletes)

    conn = get_db_connection()
    cur = conn.cursor()

    # Both ffa_ids should exist (ffa_id is unique, not license_id)
    cur.execute("SELECT COUNT(*) FROM athletes WHERE license_id = ?", ("L123",))
    count = cur.fetchone()[0]

    cur.execute("SELECT ffa_id FROM athletes WHERE ffa_id = ?", ("OLD123",))
    old_exists = cur.fetchone() is not None

    cur.execute("SELECT ffa_id FROM athletes WHERE ffa_id = ?", ("NEW456",))
    new_exists = cur.fetchone() is not None

    conn.close()

    # Both should exist with new schema
    assert count == 2
    assert old_exists
    assert new_exists


def test_athlete_without_license_id(db_dsn):
    """Test storing an athlete without license_id"""
    athletes = {
        "NO_LICENSE": {
            "name": "No License Athlete",
            "url": "http://example.com/no_license",
            "birth_date": "2000",
            "license_id": None,
            "sexe": "F",
            "nationality": "FRA",
        }
    }
    store_athletes(athletes)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT ffa_id, name FROM athletes WHERE ffa_id = ?", ("NO_LICENSE",))
    row = cur.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "NO_LICENSE"
    assert row[1] == "No License Athlete"


def test_add_license_id_to_existing_athlete(db_dsn):
    """Test adding license_id to an existing athlete that didn't have one"""
    # Insert without license_id
    athletes = {
        "ATHLETE1": {
            "name": "Test Athlete",
            "url": "http://example.com/1",
            "birth_date": "2000",
            "license_id": None,
            "sexe": "M",
            "nationality": "FRA",
        }
    }
    store_athletes(athletes)

    # Update with license_id
    athletes = {
        "ATHLETE1": {
            "name": "Test Athlete",
            "url": "http://example.com/1",
            "birth_date": "2000",
            "license_id": "L777",
            "sexe": "M",
            "nationality": "FRA",
        }
    }
    store_athletes(athletes)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT license_id FROM athletes WHERE ffa_id = ?", ("ATHLETE1",))
    license_id = cur.fetchone()[0]
    conn.close()

    assert license_id == "L777"


def test_athlete_with_dash_license_id(db_dsn):
    """Test that license_id with value '-' is treated as invalid"""
    athletes = {
        "DASH1": {
            "name": "Athlete With Dash",
            "url": "http://example.com/dash",
            "birth_date": "2000",
            "license_id": "-",
            "sexe": "M",
            "nationality": "FRA",
        }
    }
    store_athletes(athletes)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT ffa_id, name, license_id FROM athletes WHERE ffa_id = ?", ("DASH1",))
    row = cur.fetchone()
    conn.close()

    # Athlete should be stored but '-' is treated as invalid license_id
    assert row is not None
    assert row[0] == "DASH1"
    assert row[2] == "-"  # Stored as is but treated as invalid


def test_no_duplicate_with_dash_license(db_dsn):
    """Test that two athletes with '-' as license_id don't conflict"""
    # Insert two different athletes both with license_id = '-'
    athletes = {
        "ATHLETE_A": {
            "name": "Athlete A",
            "url": "http://example.com/a",
            "birth_date": "2000",
            "license_id": "-",
            "sexe": "M",
            "nationality": "FRA",
        }
    }
    store_athletes(athletes)

    athletes = {
        "ATHLETE_B": {
            "name": "Athlete B",
            "url": "http://example.com/b",
            "birth_date": "2001",
            "license_id": "-",
            "sexe": "F",
            "nationality": "FRA",
        }
    }
    store_athletes(athletes)

    conn = get_db_connection()
    cur = conn.cursor()

    # Both athletes should exist (no conflict since '-' is treated as invalid)
    cur.execute("SELECT COUNT(*) FROM athletes WHERE license_id = ?", ("-",))
    count = cur.fetchone()[0]
    conn.close()

    assert count == 2
