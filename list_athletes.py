#!/usr/bin/env python3
"""
List athletes from a PostgreSQL database containing club IDs and store them in the same database.
"""

import argparse
from datetime import datetime
import sys
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import psycopg2
import requests
from bs4 import BeautifulSoup
from common_config import get_logger, setup_logging
from db import get_db_connection, create_database, DatabaseConnectionError

logger = get_logger(__name__)

# URL of the club
CLUB_URL = 'https://www.athle.fr/bases/liste.aspx?frmbase=cclubs&frmmode=2&frmespace=&frmtypeclub=M&frmsaison={year}&frmnclub={club_id}&frmposition={page}'
ATHLETE_BASE_URL = 'https://www.athle.fr/athletes/{athlete_id}'
SESSION = requests.Session()
adapter = HTTPAdapter = requests.adapters.HTTPAdapter(
    pool_connections=24,
    pool_maxsize=24,
)
SESSION.mount('https://', adapter)

# First year of the database
FIRST_YEAR = 2004

total_athletes = 0

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

def fetch_and_parse_html(url: str, max_retries: int = 3) -> BeautifulSoup | None:
    """
    Fetch and parse the HTML content of a URL with retry logic
    Args:
        url (str): The URL to fetch
        max_retries (int): Maximum number of retry attempts
    Returns:
        BeautifulSoup: The parsed HTML content, or None if all retries failed
    """
    for attempt in range(max_retries):
        try:
            response = SESSION.get(url, timeout=20)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'lxml')
        except requests.Timeout:
            logger.warning("Timeout fetching %s (attempt %d/%d)", url, attempt + 1, max_retries)
            if attempt == max_retries - 1:
                logger.error("Failed to fetch %s after %d attempts (timeout)", url, max_retries)
                return None
        except requests.HTTPError as e:
            logger.error("HTTP error fetching %s: %s", url, e)
            return None
        except requests.RequestException as e:
            logger.warning("Error fetching %s: %s (attempt %d/%d)", url, e, attempt + 1, max_retries)
            if attempt == max_retries - 1:
                logger.error("Failed to fetch %s after %d attempts", url, max_retries)
                return None
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
    Check if an athlete already exists in the PostgreSQL database.
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
        logger.error("Error: %s", e)
        raise
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
                url = ATHLETE_BASE_URL.format(athlete_id=id_athlete)
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
        athlete_links = soup.find_all('a', href=lambda x: x and 'athletes' in x)

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
    id_athlete = link['href'].split('/')[2].strip()

    logger.debug("Processing athlete ID: %s", id_athlete)

    if athlete_exists(id_athlete):
        return None

    name_athlete = link.get_text(strip=True)
    # url = ATHLETE_BASE_URL.format(athlete_id=convert_athlete_id(id_athlete))
    url = ATHLETE_BASE_URL.format(athlete_id=id_athlete)

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
    Store the athletes in the PostgreSQL database
    Args:
        athletes (dict): The athletes
    """
    global total_athletes
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
        logger.info("Inserted %s athletes into the database", len(athletes))
        total_athletes += len(athletes)
    except psycopg2.Error as e:
        logger.error("Error: %s", e)
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
        with open('log.txt', 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now()} - {len(athletes)} athletes stored\n")

def create_athletes_table():
    """
    Create the athletes table in the PostgreSQL database
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
        logger.error("Error: %s", e)
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def retrieve_clubs(club_id: str, year: int) -> dict:
    """
    Retrieve the clubs from the PostgreSQL database only if the last year is greater or equal to the given year
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
        logger.error("Error: %s", e)
        raise
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
        return extract_athlete_data_parallel(athletes, soup)
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

    # Normaliser tous les <p class="text-white"> en une liste de lignes lisibles
    lines = []
    if soup:
        lines = [p.get_text(" ", strip=True) for p in soup.select("p.text-white")]

    for line in lines:
        # Année de naissance: "Né(e) en : 2004"
        if line.startswith("Né(e) en"):
            m = re.search(r"\b(19|20)\d{2}\b", line)
            if m:
                birth_date = m.group(0)
            continue

        # Catégorie / Nationalité : "ES / F / FRA"
        if line.startswith("Catégorie / Nationalité"):
            # On récupère les trois champs séparés par "/"
            # ex: "Catégorie / Nationalité : ES / F / FRA"
            # -> cat='ES', sex='F', nat='FRA'
            parts = [x.strip() for x in line.split(": ", 1)[1].split("/")]
            if len(parts) >= 3:
                sex = parts[1]
                nat = parts[2]
                # Nettoyage simple
                sex = re.sub(r"[^A-Za-z]", "", sex)[:1] or None
                nat = re.sub(r"[^A-Za-z]", "", nat)[:3].upper() or None
                sexe = sex
                nationality = nat
            continue

        # N° de licence : "N° de licence : 2387169 - COMP (maj le ...)"
        if line.startswith("N° de licence"):
            m = re.search(r"\b\d{5,}\b", line)  # n° numérique
            if m:
                license_number = m.group(0)
            continue

    return birth_date, license_number, sexe, nationality

def update_athletes_info():
    """
    Update missing information for all athletes in the PostgreSQL database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Sélectionner tous les athlètes qui ont des informations manquantes
    cursor.execute("SELECT id, url FROM athletes WHERE url IS NULL OR url = ''")
    athletes_to_update = cursor.fetchall()
    logger.info("Updating information for %s athletes", len(athletes_to_update))

    cpt = 0
    # Utiliser ThreadPoolExecutor pour paralléliser les mises à jour
    with ThreadPoolExecutor(max_workers=10) as executor:
        # with ThreadPoolExecutor(max_workers=1) as executor:
        future_to_id = {executor.submit(fetch_and_update_athlete, athlete_id): athlete_id for (athlete_id, _) in athletes_to_update}
        for future in as_completed(future_to_id):
            try:
                cpt += 1
                logger.info("%s / %s - Updated athlete %s", cpt, len(athletes_to_update), future_to_id[future])
                future.result()  # Just to catch any exceptions that might have been thrown
            except Exception as e:
                logger.error("Failed to update athlete %s: %s", future_to_id[future], str(e))
                raise
    conn.close()

def fetch_and_update_athlete(athlete_id):
    """
    Fetch and update athlete data for a given athlete ID in the PostgreSQL database.
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
    Process the clubs and athletes and store them in the PostgreSQL database
    Args:
        first_year (int): The first year
        last_year (int): The last year
        club_id (str): The club ID
    """
    try:
        create_athletes_table()
        logger.info("Processing years from %s to %s", first_year, last_year)
        for year in range(first_year, last_year + 1):
            clubs = retrieve_clubs(club_id, year)
            nb_clubs = len(clubs)
            logger.info("Year %s: Found %s clubs to process", year, nb_clubs)
            cpt = 0

            for club in clubs:
                cpt += 1
                try:
                    logger.info("%s / %s - Processing club %s for year %s", cpt, nb_clubs, clubs[club], year)
                except UnicodeEncodeError:
                    logger.error("UnicodeEncodeError for %s", club)
                    raise
                athletes = extract_athletes_from_club(year, club)
                store_athletes(athletes)
    except KeyboardInterrupt:
        logger.error("Interrupted by user")
        raise
    except requests.RequestException as e:
        logger.error("Error: %s", e)
        raise

def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(
            description="List athletes from a PostgreSQL database containing club IDs.")
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
    last_year = max(first_year, args.last_year)

    logger.info("Start scrapping")

    try:
        create_database()
    except DatabaseConnectionError as e:
        logger.error(str(e))
        sys.exit(1)

    if args.update:
        update_athletes_info()
    else:
        process_clubs_and_athletes(first_year, last_year, args.club_id)
        logger.info("Scrapping terminé : %s athlètes", total_athletes)

if __name__ == '__main__':
    setup_logging()
    logger.info("Script started with args: %s", ' '.join(sys.argv))
    main()
