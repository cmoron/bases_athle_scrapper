import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.db import get_db_connection
from scraper.list_clubs import store_clubs
from scraper.list_athletes import store_athletes


def create_test_schema(conn):
    """Create a simplified schema for SQLite tests (without PostgreSQL-specific features)"""
    cursor = conn.cursor()

    # Simplified clubs table for tests
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clubs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ffa_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            normalized_name TEXT NOT NULL,
            first_year INTEGER,
            last_year INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Simplified athletes table for tests
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


def test_store_clubs(db_dsn):
    clubs = {
        "1": ("Club One", 2000, 2001),
        "2": ("Club Two", 2002, 2003),
    }
    store_clubs(clubs)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT ffa_id, name, first_year, last_year FROM clubs ORDER BY ffa_id")
    rows = cur.fetchall()
    conn.close()
    assert len(rows) == 2
    assert rows[0][0] == "1"
    assert rows[0][1] == "Club One"
    assert rows[1][0] == "2"
    assert rows[1][1] == "Club Two"


def test_store_athletes(db_dsn):
    athletes = {
        "ath1": {
            "name": "Athlete One",
            "url": "http://example.com",
            "birth_date": "2000-01-01",
            "license_id": "L1",
            "sexe": "M",
            "nationality": "FR",
        }
    }
    store_athletes(athletes)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT ffa_id, name, url, birth_date, license_id, sexe, nationality FROM athletes"
    )
    rows = cur.fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0][0] == "ath1"
    assert rows[0][1] == "Athlete One"
    assert rows[0][4] == "L1"
