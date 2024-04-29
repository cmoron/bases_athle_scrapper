#!/usr/bin/env python3
"""
List athletes from a SQLite database file containing clubs id.
"""

import argparse
from datetime import datetime
import sqlite3
import sys
import requests
from bs4 import BeautifulSoup

# URL of the club
CLUB_URL = 'https://bases.athle.fr/asp.net/liste.aspx?frmpostback=true&frmbase=resultats&frmmode=1&frmespace=0&frmsaison={year}&frmclub={club_id}&frmposition={page}'

# First year of the database
FIRST_YEAR = 2004

def generate_club_url(year: int, club_id: str, page: int = 0) -> str:
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

def fetch_and_parse_html(url: str) -> BeautifulSoup:
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
    Get the number of club pages for a given year
    Args:
        soup (BeautifulSoup): The BeautifulSoup object
    Returns:
        int: Number of club pages
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
            id_athlete = link['href'].split(',')[1].strip("'")
            name_athlete = link.get_text(strip=True)
            athletes[id_athlete] = name_athlete
    return athletes

def store_athletes(athletes: dict, cursor: sqlite3.Cursor):
    """
    Store the athletes in the database
    Args:
        athletes (dict): The athletes
        cursor (sqlite3.Cursor): The cursor to execute SQL commands
    """
    cursor.executemany(
        'INSERT OR IGNORE INTO athletes (id, name) VALUES (?, ?)',
        list(athletes.items())
    )

def create_athletes_table(cursor: sqlite3.Cursor):
    """
    Create the athletes table
    Args:
        cursor (sqlite3.Cursor): The cursor to execute SQL commands
    """
    cursor.execute('CREATE TABLE IF NOT EXISTS athletes (id TEXT PRIMARY KEY, name TEXT)')

def retrieve_clubs(cursor: sqlite3.Cursor, club_id: str, year: int) -> dict:
    """
    Retrieve the clubs from the database only if the last year is greater or equal to the given year
    Args:
        cursor (sqlite3.Cursor): The cursor to execute SQL commands
        club_id (str): The club ID
        year (int): The year
    Returns:
        dict: The clubs
    """
    if club_id:
        cursor.execute('SELECT id, name FROM clubs WHERE id = ?', (club_id,))
    else:
        cursor.execute('SELECT id, name FROM clubs WHERE first_year <= ? AND last_year >= ?', (year, year))
    return dict(cursor.fetchall())

def extract_athletes_from_club(year: int, club_id: str) -> dict:
    """
    Extract athletes from a club
    Args:
        year (int): The year
        club_id (str): The club ID
    Returns:
        dict: The athletes
    """
    athletes = {}
    url = generate_club_url(year, club_id)
    soup = fetch_and_parse_html(url)
    if soup:
        max_pages = get_max_pages(soup)
        for page in range(max_pages):
            paginate_url = generate_club_url(year, club_id, page)
            paginate_soup = fetch_and_parse_html(paginate_url)
            athletes.update(extract_athlete_data({}, paginate_soup))
    return athletes

def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(description="List athletes from a SQLite database file containing clubs id.")
    parser.add_argument('--first-year', type=int, default=FIRST_YEAR, help='First year of the database.')
    parser.add_argument('--last-year', type=int, default=datetime.now().year, help='Last year of the database.')
    parser.add_argument('--club-id', type=str, help='Club ID to extract athletes from.')
    parser.add_argument('database', type=str, help='Path to the SQLite3 clubs database file.')
    args = parser.parse_args()
    first_year = args.first_year
    last_year = args.last_year

    try:
        with sqlite3.connect(args.database) as conn:
            cursor = conn.cursor()
            create_athletes_table(cursor)
            for year in range(first_year, last_year + 1):
                clubs = retrieve_clubs(cursor, args.club_id, year)
                nb_clubs = len(clubs)
                cpt = 0

                for club_id in clubs:
                    cpt += 1
                    print(f"{cpt} / {nb_clubs} - Processing club {clubs[club_id]} for year {year}")
                    athletes = extract_athletes_from_club(year, club_id)
                    store_athletes(athletes, cursor)
            conn.commit()
    except FileNotFoundError:
        print(f"Error: File {args.database} not found.", file=sys.stderr)
    except requests.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
    except sqlite3.Error as e:
        print(f"Error: {e}", file=sys.stderr)

if __name__ == '__main__':
    main()
