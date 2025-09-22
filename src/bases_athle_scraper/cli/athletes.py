"""Command-line helpers for scraping athletes."""

from __future__ import annotations

import argparse
from datetime import datetime
import logging
from typing import Sequence

import requests

from ..athletes import FIRST_YEAR, scrape_athletes
from ..database import create_database

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the athletes CLI."""

    parser = argparse.ArgumentParser(
        description="List athletes from a PostgreSQL database containing club IDs.",
    )
    parser.add_argument(
        "--first-year",
        type=int,
        default=FIRST_YEAR,
        help="Première saison à collecter.",
    )
    parser.add_argument(
        "--last-year",
        type=int,
        default=datetime.now().year,
        help="Dernière saison à collecter (inclus).",
    )
    parser.add_argument(
        "--club-id",
        type=str,
        help="Identifiant du club à extraire.",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Mettre à jour les informations manquantes des athlètes existants uniquement.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI command for athlete scraping."""

    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(filename="update.log", level=logging.INFO)

    try:
        create_database()
        scrape_athletes(
            first_year=args.first_year,
            last_year=args.last_year,
            club_id=args.club_id,
            update=args.update,
        )
    except KeyboardInterrupt:  # pragma: no cover - manual interruption
        LOGGER.warning("Interruption par l'utilisateur")
        return 1
    except requests.RequestException as exc:  # pragma: no cover - network errors
        LOGGER.error("Erreur lors de la requête : %s", exc)
        return 1

    return 0
