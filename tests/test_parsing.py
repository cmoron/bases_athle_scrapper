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

def test_extract_athlete_data_parallel(monkeypatch):
    html = (FIXTURES / "club_athletes.html").read_text()
    soup = BeautifulSoup(html, "html.parser")

    def fake_extract(url):
        return "2004", "2387169", "F", "FRA"

    monkeypatch.setattr(list_athletes, "extract_birth_date_and_license", fake_extract)
    athletes = list_athletes.extract_athlete_data_parallel({}, soup)
    from pprint import pprint
    pprint(athletes)
    expected_url = list_athletes.ATHLETE_BASE_URL.format(
        athlete_id="974476"
    )
    assert athletes == {
        "974476": {
            "id": "974476",
            "name": "DOE Jane",
            "url": expected_url,
            "birth_date": "2004",
            "license_id": "2387169",
            "sexe": "F",
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
    assert birth_date == "2004"
    assert license_id == "2387169"
    assert sexe == "F"
    assert nationality == "FRA"
