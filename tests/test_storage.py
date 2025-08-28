import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db import get_db_connection
from list_clubs import store_clubs
from list_athletes import store_athletes, create_athletes_table


@pytest.fixture
def db_dsn(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    dsn = f"sqlite:///{db_file}"
    monkeypatch.setenv("DATABASE_URL", dsn)
    yield dsn
    if db_file.exists():
        db_file.unlink()
    log = tmp_path / "log.txt"
    if log.exists():
        log.unlink()


def test_store_clubs(db_dsn):
    clubs = {
        "1": ("Club One", 2000, 2001),
        "2": ("Club Two", 2002, 2003),
    }
    store_clubs(clubs)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, first_year, last_year FROM clubs ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    assert rows == [
        ("1", "Club One", 2000, 2001),
        ("2", "Club Two", 2002, 2003),
    ]


def test_store_athletes(db_dsn):
    create_athletes_table()
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
        "SELECT id, name, url, birth_date, license_id, sexe, nationality FROM athletes"
    )
    rows = cur.fetchall()
    conn.close()
    assert rows == [
        (
            "ath1",
            "Athlete One",
            "http://example.com",
            "2000-01-01",
            "L1",
            "M",
            "FR",
        )
    ]
