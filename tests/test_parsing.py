import pathlib

from bs4 import BeautifulSoup

from bases_athle_scrapper import athletes
from bases_athle_scrapper import clubs as clubs_module

FIXTURES = pathlib.Path(__file__).parent / "fixtures"

def test_extract_clubs_from_page():
    html = (FIXTURES / "clubs.html").read_text()
    soup = BeautifulSoup(html, "html.parser")
    club_map = clubs_module.extract_clubs_from_page(soup)
    assert club_map == {"1234": "Club Name", "5678": "Second Club"}

def test_extract_athlete_data_parallel(monkeypatch):
    html = (FIXTURES / "club_athletes.html").read_text()
    soup = BeautifulSoup(html, "html.parser")

    def fake_extract(url):
        return "2004", "2387169", "F", "FRA"

    monkeypatch.setattr(athletes, "extract_birth_date_and_license", fake_extract)
    monkeypatch.setattr(athletes, "athlete_exists", lambda _id: False)
    athletes_data = athletes.extract_athlete_data_parallel({}, soup)
    expected_url = athletes.ATHLETE_BASE_URL.format(
        athlete_id="974476"
    )
    assert athletes_data == {
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

    monkeypatch.setattr(athletes, "fetch_and_parse_html", fake_fetch)
    birth_date, license_id, sexe, nationality = athletes.extract_birth_date_and_license("dummy")
    assert birth_date == "2004"
    assert license_id == "2387169"
    assert sexe == "F"
    assert nationality == "FRA"
