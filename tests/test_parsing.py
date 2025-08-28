import pathlib
import sys
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

import list_clubs
import list_athletes

FIXTURES = pathlib.Path(__file__).parent / "fixtures"

def test_extract_clubs_from_page():
    html = (FIXTURES / "clubs.html").read_text()
    soup = BeautifulSoup(html, "html.parser")
    clubs = list_clubs.extract_clubs_from_page(soup)
    assert clubs == {"1234": "Club Name", "5678": "Second Club"}

def test_extract_athlete_data(monkeypatch):
    html = (FIXTURES / "club_athletes.html").read_text()
    soup = BeautifulSoup(html, "html.parser")

    def fake_extract(url):
        return "01/01/1990", "LIC123", "M", "FRA"

    monkeypatch.setattr(list_athletes, "extract_birth_date_and_license", fake_extract)
    athletes = list_athletes.extract_athlete_data({}, soup)
    expected_url = list_athletes.ATHLETE_BASE_URL.format(
        athlete_id=list_athletes.convert_athlete_id("5678")
    )
    assert athletes == {
        "5678": {
            "name": "John Doe",
            "url": expected_url,
            "birth_date": "01/01/1990",
            "license_id": "LIC123",
            "sexe": "M",
            "nationality": "FRA",
        },
        "91011": {
            "name": "Jane Roe",
            "url": list_athletes.ATHLETE_BASE_URL.format(
                athlete_id=list_athletes.convert_athlete_id("91011")
            ),
            "birth_date": "01/01/1990",
            "license_id": "LIC123",
            "sexe": "M",
            "nationality": "FRA",
        },
    }

def test_extract_birth_date_and_license(monkeypatch):
    html = (FIXTURES / "athlete.html").read_text()
    soup = BeautifulSoup(html, "lxml")

    def fake_fetch(url):
        return soup

    monkeypatch.setattr(list_athletes, "fetch_and_parse_html", fake_fetch)
    birth_date, license_id, sexe, nationality = list_athletes.extract_birth_date_and_license("dummy")
    assert birth_date == "01/01/1990"
    assert license_id == "LIC123"
    assert sexe == "M"
    assert nationality == "FRA"
