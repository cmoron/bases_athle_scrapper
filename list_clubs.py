#!/usr/bin/env python3
"""
Récupère les données des clubs d'athlétisme pour une année donnée
"""

import argparse
from datetime import datetime
import re
import sqlite3
import sys
import requests
from bs4 import BeautifulSoup

# URL de la base de données des clubs d'athlétisme
FIRST_YEAR = 2004
BASES_ATHLE_URL = 'https://bases.athle.fr'

def get_max_club_pages(year: int) -> int:
    """
    Récupère le nombre de pages de clubs pour une année donnée
    Args:
        year (int): Année pour laquelle récupérer les données

    Returns:
        int: Nombre de pages de clubs
    """
    max_pages = 0
    club_base_url = BASES_ATHLE_URL + f'/asp.net/liste.aspx?frmpostback=true&frmbase=cclubs&frmmode=1&frmespace=0&frmsaison={year}&frmposition='
    response = requests.get(club_base_url, timeout=5)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    select_element = soup.find('select', class_='barSelect')

    if select_element:
        max_pages = len(select_element.find_all('option'))

    return max_pages

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
    club_base_url = BASES_ATHLE_URL + f'/asp.net/liste.aspx?frmpostback=true&frmbase=cclubs&frmmode=1&frmespace=0&frmsaison={year}&frmposition='

    for page in range(max_club_pages):
        url = club_base_url + str(page)
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        club_link_elements = soup.find_all('td', class_=re.compile(r'datas1[01]'))

        for club_link_element in club_link_elements:
            club_link = club_link_element.find('a')
            if club_link:
                club_name = club_link.text.strip().rstrip('*').strip()
                url= club_link['href']
                match = re.search(r'&frmnclub=(\d+)&', url)
                if match:
                    club_id = match.group(1)
                    if club_id not in clubs:
                        clubs[club_id] = (club_name, year, year)
                    else:
                        clubs[club_id] = (club_name, min(clubs[club_id][1], year), max(clubs[club_id][2], year))

    return clubs

def store_clubs(database: str, clubs: dict):
    """
    Stocke les clubs dans une base de données

    Args:
        database (str): Chemin vers la base de données SQLite3
        clubs (dict): Dictionnaire des clubs
    """
    # Create a sqlite3 database to store clubs
    with sqlite3.connect(database) as conn:
        cursor = conn.cursor()
        # Create a table to store clubs only if it does not exist
        cursor.execute('CREATE TABLE IF NOT EXISTS clubs (id TEXT PRIMARY KEY, name TEXT, first_year INTEGER DEFAULT 0, last_year INTEGER DEFAULT 0)')

        for club_id, club in clubs.items():
            name = club[0]
            first_year = club[1]
            last_year = club[2]

            # Insert the club if it does not exist
            cursor.execute('INSERT OR IGNORE INTO clubs (id, name, first_year, last_year) VALUES (?, ?, ?, ?)', (club_id, name, first_year, last_year))

def main():
    """
    Fonction principale
    """
    parser = argparse.ArgumentParser(
        description="Récupère les données des clubs d'athlétisme FFA sur bases.athle")
    parser.add_argument('database', type=str, help='Path to the SQLite3 clubs database file.')
    args = parser.parse_args()
    current_year = datetime.now().year

    try:
        # for each year from FIRST_YEAR to current year
        clubs = {}
        for year in range(FIRST_YEAR, current_year + 1):
            clubs = extract_clubs(clubs, year)

        store_clubs(args.database, clubs)
    except requests.RequestException as e:
        print(f"Erreur lors de la requête : {e}", file=sys.stderr)

if __name__ == '__main__':
    main()
