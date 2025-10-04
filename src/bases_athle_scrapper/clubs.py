"""Utilities to fetch and persist club information."""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict

import requests
from bs4 import BeautifulSoup

from .database import get_db_connection
from .logging_config import get_logger

# URL de la base de données des clubs d'athlétisme
FIRST_YEAR = 2004
BASES_ATHLE_URL = 'https://www.athle.fr/bases/'
SESSION = requests.Session()

logger = get_logger(__name__)

def get_max_club_pages(year: int) -> int:
    """
    Récupère le nombre de pages de clubs pour une année donnée
    Args:
        year (int): Année pour laquelle récupérer les données

    Returns:
        int: Nombre de pages de clubs
    """
    max_pages = 0
    club_base_url = BASES_ATHLE_URL + f'/liste.aspx?frmpostback=true&frmbase=cclubs&frmmode=1&frmespace=0&frmsaison={year}&frmsexe=&frmligue=&frmdepartement=&frmnclub=&frmruptures='

    response = SESSION.get(club_base_url, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    select_element = soup.find('div', id='optionsPagination')

    if select_element:
        max_pages = len(select_element.find_all('div', class_='select-option'))

    return max_pages

def fetch_club_page(url: str) -> BeautifulSoup:
    """
    Fetch and parse the HTML content of a URL
    Args:
        url (str): The URL to fetch
    Returns:
        BeautifulSoup: The parsed HTML content
    """
    try:
        response = SESSION.get(url, timeout=20)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        logger.error("Error fetching %s: %s", url, e)
        return None

def extract_clubs_from_page(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Extract clubs from a BeautifulSoup object
    Args:
        soup (BeautifulSoup): The BeautifulSoup object
    Returns:
        dict: Dictionary of clubs
    """
    tbody = soup.find("tbody", class_="text-blue-primary") or soup

    clubs: dict[str, str] = {}

    # Les lignes utiles ont exactement 7 <td> au niveau racine (pas les detail-row).
    for tr in tbody.find_all("tr"):
        tds = tr.find_all("td", recursive=False)
        if len(tds) != 7:
            continue

        name_td = tds[2]  # colonne "Club" (contient un <a>)
        id_td = tds[3]    # colonne "N°Club"

        a = name_td.find("a")
        if not a:
            continue

        club_name = " ".join(a.get_text(strip=True).split())
        club_name = re.sub(r"\*+$", "", club_name).strip()  # retire les astérisques finaux
        club_id = id_td.get_text(strip=True)

        if club_id and club_name:
            clubs[club_id] = club_name

    return clubs


def extract_clubs(clubs: Dict[str, tuple[str, int, int]], year: int) -> Dict[str, tuple[str, int, int]]:
    """
    Récupère les clubs d'athlétisme pour une année donnée
    Args:
        year (int): Année pour laquelle récupérer les données
    Returns:
        dict: Dictionnaire des clubs d'athlétisme avec leur ID comme clé
              et leur nom et année comme valeur
    """
    max_club_pages = get_max_club_pages(year)
    club_base_url = BASES_ATHLE_URL + f'/liste.aspx?frmpostback=true&frmbase=cclubs&frmmode=1&frmespace=0&frmsaison={year}&frmsexe=&frmligue=&frmdepartement=&frmnclub=&frmruptures=&frmposition='
    urls = [club_base_url + str(page) for page in range(max_club_pages)]

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(fetch_club_page, url): url for url in urls}
        for future in as_completed(future_to_url):
            try:
                soup = future.result()
                if soup:
                    page_clubs = extract_clubs_from_page(soup)
                    for club_id, club_name in page_clubs.items():
                        if club_id not in clubs:
                            clubs[club_id] = (club_name, year, year)
                        else:
                            clubs[club_id] = (club_name, min(clubs[club_id][1], year), max(clubs[club_id][2], year))
                        logger.debug("Fetched club %s: %s", club_id, clubs[club_id])
            except requests.RequestException as e:
                logger.error("Request error for URL %s: %s", future_to_url[future], e)

    return clubs

def store_clubs(clubs: Dict[str, tuple[str, int, int]]) -> None:
    """
    Stocke les clubs dans une base de données PostgreSQL.

    Args:
        clubs (dict): Dictionnaire des clubs
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS clubs (
            id TEXT PRIMARY KEY,
            name TEXT,
            first_year INTEGER DEFAULT 0,
            last_year INTEGER DEFAULT 0
        )
        """
    )

    for club_id, club in clubs.items():
        name, first_year, last_year = club

        cursor.execute(
            """
            INSERT INTO clubs (id, name, first_year, last_year)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (club_id, name, first_year, last_year),
        )

    conn.commit()
    cursor.close()
    conn.close()
