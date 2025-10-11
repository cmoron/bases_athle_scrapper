#!/usr/bin/env python3
"""
Récupère les données des clubs d'athlétisme pour une année donnée et les stocke dans une base de données PostgreSQL.
"""

import argparse
from datetime import datetime
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from common_config import get_logger, setup_logging
from db import get_db_connection, create_database

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

def extract_clubs_from_page(soup: BeautifulSoup) -> dict:
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


def extract_clubs(clubs: dict, year: int) -> dict:
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

def store_clubs(clubs: dict):
    """
    Stocke les clubs dans une base de données PostgreSQL.

    Args:
        clubs (dict): Dictionnaire des clubs
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clubs (
            id TEXT PRIMARY KEY,
            name TEXT,
            first_year INTEGER DEFAULT 0,
            last_year INTEGER DEFAULT 0
        )
    ''')

    for club_id, club in clubs.items():
        name = club[0]
        first_year = club[1]
        last_year = club[2]

        cursor.execute('''
            INSERT INTO clubs (id, name, first_year, last_year)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        ''', (club_id, name, first_year, last_year))

    conn.commit()
    cursor.close()
    conn.close()

def main():
    """
    Fonction principale
    """
    parser = argparse.ArgumentParser(
        description="Récupère les données des clubs d'athlétisme FFA sur bases.athle")
    parser.add_argument("--first-year", type=int, default=FIRST_YEAR,
        help=f"Année de départ pour l'extraction (défaut : {FIRST_YEAR})"
    )
    args = parser.parse_args()


    # Calcul de la saison actuelle : si on est à partir de septembre, on prend année+1
    now = datetime.now()
    current_season = now.year + 1 if now.month >= 9 else now.year

    logger.info("Début de l'extraction des clubs")

    try:
        create_database()

        # for each year from FIRST_YEAR to current year
        clubs = {}
        for year in range(args.first_year, current_season + 1):
            clubs = extract_clubs(clubs, year)

        logger.info("Extraction terminée : %s clubs", len(clubs))

        store_clubs(clubs)
    except requests.RequestException as e:
        logger.error("Erreur lors de la requête : %s", e)

if __name__ == '__main__':
    setup_logging()
    main()
