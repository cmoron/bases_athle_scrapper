"""Command-line helpers for scraping clubs."""

from __future__ import annotations

import argparse
from datetime import datetime
import logging
from typing import Sequence

import requests

from ..clubs import FIRST_YEAR, sync_clubs
from ..database import create_database

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the clubs CLI."""

    parser = argparse.ArgumentParser(
        description="Récupère les données des clubs d'athlétisme FFA sur bases.athle",
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI command for club scraping."""

    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    LOGGER.info("Début de l'extraction des clubs")

    try:
        create_database()
        sync_clubs(first_year=args.first_year, last_year=args.last_year)
    except requests.RequestException as exc:  # pragma: no cover - network errors
        LOGGER.error("Erreur lors de la requête : %s", exc)
        return 1

    return 0
