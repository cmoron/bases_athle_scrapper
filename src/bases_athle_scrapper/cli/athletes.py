"""Command line interface for athlete scraping."""

from __future__ import annotations

import argparse
from datetime import datetime
from typing import Optional, Sequence

from .. import athletes as athletes_module
from ..database import create_database, DatabaseConnectionError
from ..logging_config import get_logger, setup_logging

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List athletes from a database of club IDs and persist them.",
    )
    parser.add_argument(
        "--first-year",
        type=int,
        default=athletes_module.FIRST_YEAR,
        help=f"First year to fetch (default: {athletes_module.FIRST_YEAR})",
    )
    parser.add_argument(
        "--last-year",
        type=int,
        default=datetime.now().year,
        help="Last year to fetch (default: current year)",
    )
    parser.add_argument(
        "--club-id",
        type=str,
        help="Club ID to restrict the scraping to a single club.",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update missing information for all athletes.",
    )
    return parser


def run(
    first_year: int,
    last_year: int,
    club_id: Optional[str],
    update: bool,
) -> int:
    logger.info("Start scraping athletes")

    try:
        create_database()
    except DatabaseConnectionError as exc:
        logger.error("Failed to create database: %s", exc)
        return 1

    if update:
        athletes_module.update_athletes_info()
    else:
        athletes_module.process_clubs_and_athletes(first_year, last_year, club_id)
        logger.info(
            "Scrapping terminé : %s athlètes", athletes_module.total_athletes
        )
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    setup_logging()
    args = build_parser().parse_args(argv)
    return run(args.first_year, args.last_year, args.club_id, args.update)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
