"""Utilities for scraping and storing athletics club and athlete data."""

from .athletes import (  # noqa: F401
    ATHLETE_BASE_URL,
    CLUB_URL,
    FIRST_YEAR,
    convert_athlete_id,
    create_athletes_table,
    extract_athlete_data,
    extract_athlete_data_parallel,
    extract_athletes_from_club,
    extract_birth_date_and_license,
    fetch_and_parse_html,
    generate_club_url,
    get_max_pages,
    process_clubs_and_athletes,
    retrieve_clubs,
    store_athletes,
    update_athletes_info,
)
from .clubs import extract_clubs, extract_clubs_from_page, store_clubs  # noqa: F401
from .database import (  # noqa: F401
    DatabaseConnectionError,
    create_database,
    get_db_connection,
)
from .logging_config import get_logger, setup_logging  # noqa: F401

__all__ = [
    "ATHLETE_BASE_URL",
    "CLUB_URL",
    "FIRST_YEAR",
    "DatabaseConnectionError",
    "convert_athlete_id",
    "create_athletes_table",
    "create_database",
    "extract_athlete_data",
    "extract_athlete_data_parallel",
    "extract_athletes_from_club",
    "extract_birth_date_and_license",
    "extract_clubs",
    "extract_clubs_from_page",
    "fetch_and_parse_html",
    "generate_club_url",
    "get_db_connection",
    "get_logger",
    "get_max_pages",
    "process_clubs_and_athletes",
    "retrieve_clubs",
    "setup_logging",
    "store_athletes",
    "store_clubs",
    "update_athletes_info",
]
