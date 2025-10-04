import pytest

from bases_athle_scrapper.athletes import convert_athlete_id, generate_club_url

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
        == "https://www.athle.fr/bases/liste.aspx?frmbase=cclubs&frmmode=2&frmespace=&frmtypeclub=M&frmsaison=2024&frmnclub=CLUB42&frmposition=0"
    )


def test_generate_club_url_custom_page():
    """Generate a club URL with a custom page."""
    url = generate_club_url(2023, "CLUB42", page=5)
    assert (
        url
        == "https://www.athle.fr/bases/liste.aspx?frmbase=cclubs&frmmode=2&frmespace=&frmtypeclub=M&frmsaison=2023&frmnclub=CLUB42&frmposition=5"
    )
