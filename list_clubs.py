#!/usr/bin/env python3
"""
Récupère les données des clubs d'athlétisme pour une année donnée
"""

import argparse
from datetime import datetime
import re
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from db import get_db_connection, create_database

# URL de la base de données des clubs d'athlétisme
FIRST_YEAR = 2004
BASES_ATHLE_URL = 'https://bases.athle.fr'
SESSION = requests.Session()

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
    response = SESSION.get(club_base_url, timeout=5)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    select_element = soup.find('select', class_='barSelect')

    if select_element:
        max_pages = len(select_element.find_all('option'))

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
        response = SESSION.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None

def extract_clubs_from_page(soup: BeautifulSoup) -> dict:
    """
    Extract clubs from a BeautifulSoup object
    Args:
        soup (BeautifulSoup): The BeautifulSoup object
    Returns:
        dict: Dictionary of clubs
    """
    clubs = {}
    club_link_elements = soup.find_all('td', class_=re.compile(r'datas1[01]'))
    for club_link_element in club_link_elements:
        club_link = club_link_element.find('a')
        if club_link:
            club_name = club_link.text.strip().rstrip('*').strip()
            url = club_link['href']
            match = re.search(r'&frmnclub=(\d+)&', url)
            if match:
                club_id = match.group(1)
                if club_id not in clubs:
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
    club_base_url = BASES_ATHLE_URL + f'/asp.net/liste.aspx?frmpostback=true&frmbase=cclubs&frmmode=1&frmespace=0&frmsaison={year}&frmposition='
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
            except Exception as e:
                print(f"Error processing URL {future_to_url[future]}: {e}", file=sys.stderr)

    return clubs


# def extract_clubs(clubs: dict, year: int) -> dict:
    # """
    # Récupère les clubs d'athlétisme pour une année donnée

    # Args:
        # year (int): Année pour laquelle récupérer les données

    # Returns:
        # dict: Dictionnaire des clubs d'athlétisme avec leur ID comme clé
              # et leur nom et année comme valeur
    # """
    # max_club_pages = get_max_club_pages(year)
    # club_base_url = BASES_ATHLE_URL + f'/asp.net/liste.aspx?frmpostback=true&frmbase=cclubs&frmmode=1&frmespace=0&frmsaison={year}&frmposition='

    # for page in range(max_club_pages):
        # url = club_base_url + str(page)
        # response = requests.get(url, timeout=5)
        # response.raise_for_status()

        # html_content = response.text
        # soup = BeautifulSoup(html_content, 'html.parser')
        # club_link_elements = soup.find_all('td', class_=re.compile(r'datas1[01]'))

        # for club_link_element in club_link_elements:
            # club_link = club_link_element.find('a')
            # if club_link:
                # club_name = club_link.text.strip().rstrip('*').strip()
                # url= club_link['href']
                # match = re.search(r'&frmnclub=(\d+)&', url)
                # if match:
                    # club_id = match.group(1)
                    # if club_id not in clubs:
                        # clubs[club_id] = (club_name, year, year)
                    # else:
                        # clubs[club_id] = (club_name, min(clubs[club_id][1], year), max(clubs[club_id][2], year))

    # return clubs

def store_clubs(clubs: dict):
    """
    Stocke les clubs dans une base de données

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
    parser.parse_args()
    current_year = datetime.now().year

    try:
        create_database()

        # for each year from FIRST_YEAR to current year
        clubs = {}
        for year in range(FIRST_YEAR, current_year + 1):
            clubs = extract_clubs(clubs, year)

        store_clubs(clubs)
    except requests.RequestException as e:
        print(f"Erreur lors de la requête : {e}", file=sys.stderr)

if __name__ == '__main__':
    main()
