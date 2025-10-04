"""Command line interface for club scraping."""

from __future__ import annotations

import argparse
from datetime import datetime
from typing import Sequence

from .. import clubs as clubs_module
from ..database import create_database, DatabaseConnectionError
from ..logging_config import get_logger, setup_logging

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch athletics clubs from bases.athle and persist them.",
    )
    parser.add_argument(
        "--first-year",
        type=int,
        default=clubs_module.FIRST_YEAR,
        help=f"Start year for extraction (default: {clubs_module.FIRST_YEAR})",
    )
    parser.add_argument(
        "--last-year",
        type=int,
        default=datetime.now().year,
        help="Last year to fetch (default: current year)",
    )
    return parser


def run(first_year: int, last_year: int) -> int:
    logger.info("Début de l'extraction des clubs")

    try:
        create_database()
    except DatabaseConnectionError as exc:
        logger.error("Impossible de créer la base de données: %s", exc)
        return 1

    clubs: dict[str, tuple[str, int, int]] = {}
    for year in range(first_year, last_year + 1):
        clubs = clubs_module.extract_clubs(clubs, year)

    logger.info("Extraction terminée : %s clubs", len(clubs))
    clubs_module.store_clubs(clubs)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    setup_logging()
    args = build_parser().parse_args(argv)
    return run(args.first_year, args.last_year)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
