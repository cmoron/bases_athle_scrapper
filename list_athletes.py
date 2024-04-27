#!/usr/bin/env python3
"""
List athletes from a sqlite database file containing clubs id.
"""

import argparse
from datetime import datetime
import sqlite3
import sys
import requests
from bs4 import BeautifulSoup

CLUB_URL='https://bases.athle.fr/asp.net/liste.aspx?frmpostback=true&frmbase=resultats&frmmode=1&frmespace=0&frmsaison={year}&frmclub={club_id}&frmposition={page}'
FIRST_YEAR = 2004

def generate_club_url(year: int, club_id: str, page: int = 0):
    """
    Generate the URL for a club ID
    Args:
        year (int): The year
        club_id (str): The club ID
        page (int): The page number
    Returns:
        str: The URL for the club
    """
    return CLUB_URL.format(year=year, club_id=club_id, page=page)

def fetch_and_parse_html(url: str):
    """
    Fetch and parse the HTML content of a URL
    Args:
        url (str): The URL to fetch
    Returns:
        BeautifulSoup: The parsed HTML content
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raises HTTPError for bad responses
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None

def get_max_pages(soup: BeautifulSoup) -> int:
    """
    Récupère le nombre de pages de clubs pour une année donnée
    Args:
        soup (BeautifulSoup): The BeautifulSoup object

    Returns:
        int: Nombre de pages de clubs
    """
    max_pages = 0
    if soup:
        select_element = soup.find('select', class_='barSelect')

        if select_element:
            max_pages = len(select_element.find_all('option'))

    return max_pages

def extract_athlete_data(athletes: dict, soup: BeautifulSoup) -> dict:
    """
    Extract athlete data from a BeautifulSoup object
    Args:
        athletes (dict): The athletes
        soup (BeautifulSoup): The BeautifulSoup object
    Returns:
        dict: The athletes
    """
    if soup:
        athlete_links = soup.find_all('a', href=lambda x: x and 'javascript:bddThrowAthlete' in x)
        for link in athlete_links:
            id_athlete = link['href'].split(',')[1].strip()
            name_athlete = link.get_text(strip=True)
            athletes[id_athlete] =  name_athlete
    return athletes

def create_athletes_table(database):
    """
    Create the athletes table
    Args:
        database (str): The database file
    """
    with sqlite3.connect(database) as conn:
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS athletes (id TEXT PRIMARY KEY, name TEXT)')

def retrieve_clubs(database) -> dict:
    """
    Retrieve clubs from the database
    Args:
        database (str): The database file
    Returns:
        dict: The clubs
    """
    with sqlite3.connect(database) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clubs')
        return dict(cursor.fetchall())

def extract_athletes_from_club(year: int, club_id: str) -> dict:
    """
    Extract athletes from a club
    Args:
        year (int): The year
        club_id (str): The club ID
    Returns:
        dict: The athletes dictionary
    """
    athletes = {}
    url = generate_club_url(year, club_id)
    soup = fetch_and_parse_html(url)
    max_pages = get_max_pages(soup)
    for page in range(max_pages):
        paginate_url = generate_club_url(year, club_id, page)
        paginate_soup = fetch_and_parse_html(paginate_url)
        athletes = extract_athlete_data(athletes, paginate_soup)
    return athletes

def store_athletes(athletes: dict, database: str):
    """
    Store the athletes in the database
    Args:
        athletes (dict): The athletes
        database (str): The database file
    """
    with sqlite3.connect(database) as conn:
        cursor = conn.cursor()
        for athlete_id, name in athletes.items():
            cursor.execute(
                    'INSERT OR IGNORE INTO athletes (id, name) VALUES (?, ?)', (athlete_id, name))

def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(
            description="List athletes from a sqlite database file containing clubs id.")
    parser.add_argument('database', type=str, help='Path to the SQLite3 clubs database file.')
    args = parser.parse_args()
    current_year = datetime.now().year

    try:
        create_athletes_table(args.database)
        clubs = retrieve_clubs(args.database)
        nb_clubs = len(clubs)
        cpt = 0

        #extract athletes from clubs
        for club_id in clubs:
            cpt += 1
            for year in range(FIRST_YEAR, current_year + 1):
                print(cpt, "/", nb_clubs, " - Processing club", clubs[club_id], "for year", year)
                athletes = extract_athletes_from_club(year, club_id)
                store_athletes(athletes, args.database)
    except FileNotFoundError:
        print(f"Error: File {args.csv_file} not found.", file=sys.stderr)
    except requests.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
    except sqlite3.Error as e:
        print(f"Error: {e}", file=sys.stderr)

if __name__ == '__main__':
    main()
