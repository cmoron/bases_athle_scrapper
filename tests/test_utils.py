import os
import sys
import pytest

# Ensure the project root is on the Python path to allow module imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from scraper.list_athletes import generate_club_url


def test_generate_club_url_default_page():
    """Generate a club URL with the default page."""
    url = generate_club_url(2024, "CLUB42")
    assert (
        url
        == "https://www.athle.fr/bases/liste.aspx?frmbase=cclubs&frmmode=2&frmespace=&frmtypeclub=M&frmsaison=2024&frmnclub=CLUB42&frmposition=0"
    )


def test_generate_club_url_custom_page():
    """Generate a club URL with a custom page."""
    url = generate_club_url(2023, "CLUB42", page=5)
    assert (
        url
        == "https://www.athle.fr/bases/liste.aspx?frmbase=cclubs&frmmode=2&frmespace=&frmtypeclub=M&frmsaison=2023&frmnclub=CLUB42&frmposition=5"
    )
