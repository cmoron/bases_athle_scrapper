import os
import sys
import pytest

# Ensure the project root is on the Python path to allow module imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from list_athletes import convert_athlete_id, generate_club_url


@pytest.mark.parametrize(
    "athlete_id, expected",
    [
        ("1234", "5049495048514752"),
        ("ABCD", "3465336632673168"),
        ("7", "4455"),
    ],
)
def test_convert_athlete_id(athlete_id, expected):
    """Ensure convert_athlete_id returns the expected encoded string."""
    assert convert_athlete_id(athlete_id) == expected


def test_generate_club_url_default_page():
    """Generate a club URL with the default page."""
    url = generate_club_url(2024, "CLUB42")
    assert (
        url
        == "https://bases.athle.fr/asp.net/liste.aspx?frmpostback=true&frmbase=resultats&frmmode=1&frmespace=0&frmsaison=2024&frmclub=CLUB42&frmposition=0"
    )


def test_generate_club_url_custom_page():
    """Generate a club URL with a custom page."""
    url = generate_club_url(2023, "CLUB42", page=5)
    assert (
        url
        == "https://bases.athle.fr/asp.net/liste.aspx?frmpostback=true&frmbase=resultats&frmmode=1&frmespace=0&frmsaison=2023&frmclub=CLUB42&frmposition=5"
    )
