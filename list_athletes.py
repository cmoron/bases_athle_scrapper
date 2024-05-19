#!/usr/bin/env python3
"""
List athletes from a database containing clubs id.
"""

import argparse
from datetime import datetime
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import psycopg2
import requests
from bs4 import BeautifulSoup
from db import get_db_connection, create_database

# URL of the club
CLUB_URL = 'https://bases.athle.fr/asp.net/liste.aspx?frmpostback=true&frmbase=resultats&frmmode=1&frmespace=0&frmsaison={year}&frmclub={club_id}&frmposition={page}'
ATHLETE_BASE_URL = 'https://bases.athle.fr/asp.net/athletes.aspx?base=records&seq={athlete_id}'
SESSION = requests.Session()

# First year of the database
FIRST_YEAR = 2004

def convert_athlete_id(athlete_id: str) -> str:
    """
    Convert the athlete ID to a string used into athlete URL
    Args:
        athlete_id (str): The athlete ID
    Returns:
        str: The athlete ID as a string
    """
    return ''.join(f"{99 - ord(c)}{ord(c)}" for c in str(athlete_id))

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
        response = SESSION.get(url, timeout=10)
        response.raise_for_status()  # Raises HTTPError for bad responses
        return BeautifulSoup(response.text, 'lxml')
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

def athlete_exists(athlete_id: str) -> bool:
    """
    Check if an athlete already exists in the database.
    Args:
        athlete_id (str): The athlete ID
    Returns:
        bool: True if the athlete exists, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    exists = False
    try:
        cursor.execute('SELECT 1 FROM athletes WHERE id = %s', (athlete_id,))
        exists = cursor.fetchone() is not None
    except psycopg2.Error as e:
        print(f"Error: {e}", file=sys.stderr)
    finally:
        cursor.close()
        conn.close()
    return exists

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

            id_athlete = link['href'].split(',')[1].strip("'").strip()
            if id_athlete not in athletes:
                name_athlete = link.get_text(strip=True)
                # format BASE_URL with athlete_id
                url = ATHLETE_BASE_URL.format(athlete_id=convert_athlete_id(id_athlete))
                birth_date, license_id, sexe, nationality = extract_birth_date_and_license(url)
                athletes[id_athlete] = {
                        "name": name_athlete,
                        "url": url,
                        "birth_date": birth_date,
                        "license_id": license_id,
                        "sexe": sexe,
                        "nationality": nationality
                        }
    return athletes

def extract_athlete_data_parallel(athletes: dict, soup: BeautifulSoup) -> dict:
    """
    Extract athlete data from a BeautifulSoup object using parallel requests
    Args:
        athletes (dict): The athletes
        soup (BeautifulSoup): The BeautifulSoup object
    Returns:
        dict: The athletes
    """
    if soup:
        athlete_links = soup.find_all('a', href=lambda x: x and 'javascript:bddThrowAthlete' in x)

        # Préparer les tâches pour chaque athlète
        with ThreadPoolExecutor(max_workers=24) as executor:
            future_to_athlete = {executor.submit(fetch_and_extract_athlete_data, link): link for link in athlete_links}
            for future in as_completed(future_to_athlete):
                athlete_data = future.result()
                if athlete_data:
                    id_athlete = athlete_data['id']
                    if id_athlete not in athletes:
                        athletes[id_athlete] = athlete_data
    return athletes

def fetch_and_extract_athlete_data(link):
    """
    Fetch and extract athlete data from an individual athlete link
    Args:
        link (bs4.element.Tag): A BeautifulSoup tag containing the athlete link
    Returns:
        dict: Extracted data for one athlete
    """
    id_athlete = link['href'].split(',')[1].strip("'").strip()

    if athlete_exists(id_athlete):
        return None

    name_athlete = link.get_text(strip=True)
    url = ATHLETE_BASE_URL.format(athlete_id=convert_athlete_id(id_athlete))

    # Appeler une fonction pour extraire les détails de l'athlète
    birth_date, license_id, sexe, nationality = extract_birth_date_and_license(url)

    return {
        "id": id_athlete,
        "name": name_athlete,
        "url": url,
        "birth_date": birth_date,
        "license_id": license_id,
        "sexe": sexe,
        "nationality": nationality
    }

def store_athletes(athletes: dict):
    """
    Store the athletes in the database
    Args:
        athletes (dict): The athletes
    """
    athletes_data = [(
        athlete_id,
        info['name'],
        info['url'],
        info['birth_date'],
        info['license_id'],
        info['sexe'],
        info['nationality'])
        for athlete_id, info in athletes.items()
    ]

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.executemany('''
            INSERT INTO athletes (id, name, url, birth_date, license_id, sexe, nationality)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        ''', athletes_data)
        conn.commit()
    except psycopg2.Error as e:
        print(f"Error: {e}", file=sys.stderr)
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def create_athletes_table():
    """
    Create the athletes table
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS athletes (
                id TEXT PRIMARY KEY,
                name TEXT,
                license_id TEXT,
                url TEXT,
                birth_date TEXT,
                sexe TEXT,
                nationality TEXT
            )
        ''')
        conn.commit()
    except psycopg2.Error as e:
        print(f"Error: {e}", file=sys.stderr)
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def retrieve_clubs(club_id: str, year: int) -> dict:
    """
    Retrieve the clubs from the database only if the last year is greater or equal to the given year
    Args:
        club_id (str): The club ID
        year (int): The year
    Returns:
        dict: The clubs
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    res = {}
    try:
        if club_id:
            cursor.execute('SELECT id, name FROM clubs WHERE id = %s', (club_id,))
        else:
            cursor.execute('SELECT id, name FROM clubs WHERE first_year <= %s AND last_year >= %s', (year, year))
        res = dict(cursor.fetchall())
    except psycopg2.Error as e:
        print(f"Error: {e}", file=sys.stderr)
    finally:
        cursor.close()
        conn.close()
    return res

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
        urls = [generate_club_url(year, club_id, page) for page in range(max_pages)]

        # Création d'un pool de threads pour gérer les requêtes en parallèle
        with ThreadPoolExecutor(max_workers=max_pages) as executor:
            future_to_url = {executor.submit(fetch_and_parse_html, paginate_url): paginate_url for paginate_url in urls}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    page_soup = future.result()
                    if page_soup:
                        athletes.update(extract_athlete_data_parallel({}, page_soup))
                except Exception as e:
                    print(f"Error processing {url}: {e}", file=sys.stderr)
    return athletes

def extract_birth_date_and_license(url: str) -> dict:
    """
    Extract birth date and license number from the athlete's page
    Args:
        url (str): The URL of the athlete

    Returns:
        dict: Dictionary containing 'birth_date' and 'license_number'
    """
    birth_date = None
    license_number = None
    sexe = None
    nationality = None

    soup = fetch_and_parse_html(url)
    if soup:
        birth_date_td = soup.find('td', string='Né(e) en')
        if birth_date_td:
            next_td = birth_date_td.find_next_sibling('td')
            if next_td:
                birth_date_td = next_td.find_next_sibling('td')
                if birth_date_td and birth_date_td.b:
                    birth_date = birth_date_td.b.get_text(strip=True)

        license_td = soup.find('td', string='N° Licence')
        if license_td and license_td.find_next_sibling('td'):
            next_td = license_td.find_next_sibling('td')
            if next_td:
                license_td = next_td.find_next_sibling('td')
                if license_td:
                    license_number = license_td.get_text(strip=True).split(' -')[0]

        category_td = soup.find('td', string='Cat. / Nat.')
        if category_td and category_td.find_next_sibling('td'):
            next_td = category_td.find_next_sibling('td')
            if next_td:
                category_td = next_td.find_next_sibling('td')
                if category_td:
                    category_str = category_td.get_text(strip=True)
                    _, sexe, nationality = category_str.split('/')

    return birth_date, license_number, sexe, nationality

def update_athletes_info():
    """
    Update missing information for all athletes in the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Sélectionner tous les athlètes qui ont des informations manquantes
    cursor.execute("SELECT id, url FROM athletes WHERE url IS NULL OR url = ''")
    athletes_to_update = cursor.fetchall()
    print("Updating information for", len(athletes_to_update), "athletes")

    cpt = 0
    # Utiliser ThreadPoolExecutor pour paralléliser les mises à jour
    with ThreadPoolExecutor(max_workers=10) as executor:
        # with ThreadPoolExecutor(max_workers=1) as executor:
        future_to_id = {executor.submit(fetch_and_update_athlete, athlete_id): athlete_id for (athlete_id, _) in athletes_to_update}
        for future in as_completed(future_to_id):
            try:
                cpt += 1
                print(f"{cpt} / {len(athletes_to_update)} - Updated athlete {future_to_id[future]}")
                future.result()  # Just to catch any exceptions that might have been thrown
            except Exception as e:
                print(f"Failed to update athlete {future_to_id[future]}: {str(e)}")
    conn.close()

def fetch_and_update_athlete(athlete_id):
    """
    Fetch and update athlete data for a given athlete ID.
    Args:
        athlete_id (str): The athlete ID
    """
    url = ATHLETE_BASE_URL.format(athlete_id=convert_athlete_id(athlete_id))
    birth_date, license_id, sexe, nationality = extract_birth_date_and_license(url)

    # Mettre à jour la base de données
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE athletes SET url = %s, birth_date = %s, license_id = %s, sexe = %s, nationality = %s
        WHERE id = %s
    """, (url, birth_date, license_id, sexe, nationality, athlete_id))
    conn.commit()
    conn.close()

def process_clubs_and_athletes(first_year: int, last_year: int, club_id: str) -> None:
    """
    Process the clubs and athletes
    Args:
        first_year (int): The first year
        last_year (int): The last year
        club_id (str): The club ID
    """
    try:
        create_athletes_table()
        for year in range(first_year, last_year + 1):
            clubs = retrieve_clubs(club_id, year)
            nb_clubs = len(clubs)
            cpt = 0

            for club in clubs:
                cpt += 1
                try:
                    print(f"{cpt} / {nb_clubs} - Processing club {clubs[club]} for year {year}")
                except UnicodeEncodeError:
                    print(f"UnicodeEncodeError for {club}")
                athletes = extract_athletes_from_club(year, club)
                store_athletes(athletes)
    except KeyboardInterrupt:
        print("Interrupted by user")
    except requests.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)

def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(
            description="List athletes from a database file containing clubs id.")
    parser.add_argument(
            '--first-year', type=int, default=FIRST_YEAR, help='First year of the database.')
    parser.add_argument(
            '--last-year', type=int, default=datetime.now().year, help='Last year of the database.')
    parser.add_argument(
            '--club-id', type=str, help='Club ID to extract athletes from.')
    parser.add_argument(
            '--update', action='store_true', help='Update missing information for all athletes')
    args = parser.parse_args()
    first_year = args.first_year
    last_year = args.last_year

    create_database()

    if args.update:
        update_athletes_info()
    else:
        process_clubs_and_athletes(first_year, last_year, args.club_id)

if __name__ == '__main__':
    main()
