#!/usr/bin/env python3
"""
Script d'analyse consolidé de la base de données.
Affiche des statistiques et indicateurs de qualité des données.
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_logger, setup_logging
from core.db import DatabaseConnectionError, get_db_connection
from core.schema import get_table_stats

logger = get_logger(__name__)


def analyze_data_quality():
    """
    Analyse la qualité des données dans la base.

    Returns:
        dict: Indicateurs de qualité
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    quality_indicators = {}

    try:
        # ====================================================================
        # ATHLETES - Qualité des données
        # ====================================================================
        cursor.execute(
            """
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE license_id IS NOT NULL AND license_id != '' AND license_id != '-' AND license_id != 'None') as with_license,
                COUNT(*) FILTER (WHERE birth_date IS NOT NULL AND birth_date != '') as with_birth_date,
                COUNT(*) FILTER (WHERE sexe IS NOT NULL AND sexe != '') as with_sexe,
                COUNT(*) FILTER (WHERE nationality IS NOT NULL AND nationality != '') as with_nationality,
                COUNT(*) FILTER (WHERE url IS NOT NULL AND url != '') as with_url
            FROM athletes
        """
        )
        athlete_quality = cursor.fetchone()

        if athlete_quality and athlete_quality[0] > 0:
            total = athlete_quality[0]
            quality_indicators["athletes"] = {
                "total": total,
                "completeness": {
                    "license_id": round(100 * athlete_quality[1] / total, 1),
                    "birth_date": round(100 * athlete_quality[2] / total, 1),
                    "sexe": round(100 * athlete_quality[3] / total, 1),
                    "nationality": round(100 * athlete_quality[4] / total, 1),
                    "url": round(100 * athlete_quality[5] / total, 1),
                },
            }

        # Doublons potentiels (même nom + même année de naissance)
        cursor.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT normalized_name, birth_date, COUNT(*) as cnt
                FROM athletes
                WHERE birth_date IS NOT NULL AND birth_date != ''
                GROUP BY normalized_name, birth_date
                HAVING COUNT(*) > 1
            ) AS duplicates
        """
        )
        potential_duplicates = cursor.fetchone()[0]
        quality_indicators["athletes"]["potential_duplicates"] = potential_duplicates

        # ====================================================================
        # CLUBS - Qualité des données
        # ====================================================================
        cursor.execute(
            """
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE first_year IS NOT NULL) as with_first_year,
                COUNT(*) FILTER (WHERE last_year IS NOT NULL) as with_last_year,
                COUNT(*) FILTER (WHERE url IS NOT NULL AND url != '') as with_url
            FROM clubs
        """
        )
        club_quality = cursor.fetchone()

        if club_quality and club_quality[0] > 0:
            total = club_quality[0]
            quality_indicators["clubs"] = {
                "total": total,
                "completeness": {
                    "first_year": round(100 * club_quality[1] / total, 1),
                    "last_year": round(100 * club_quality[2] / total, 1),
                    "url": round(100 * club_quality[3] / total, 1),
                },
            }

        # Clubs actifs récemment
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM clubs
            WHERE last_year >= EXTRACT(YEAR FROM NOW()) - 2
        """
        )
        active_clubs = cursor.fetchone()[0]
        quality_indicators["clubs"]["active_recently"] = active_clubs

        return quality_indicators

    except Exception as e:
        logger.error(f"Error analyzing data quality: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()


def analyze_urls():
    """
    Analyse les URLs dans la base.

    Returns:
        dict: Statistiques sur les URLs
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    url_stats = {}

    try:
        # Athletes URLs
        cursor.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE url LIKE '%www.athle.fr/athletes/%') as new_format,
                COUNT(*) FILTER (WHERE url LIKE '%bases.athle.fr%') as old_format,
                COUNT(*) FILTER (WHERE url IS NULL OR url = '') as missing
            FROM athletes
        """
        )
        athlete_urls = cursor.fetchone()
        url_stats["athletes"] = {
            "new_format": athlete_urls[0],
            "old_format": athlete_urls[1],
            "missing": athlete_urls[2],
        }

        # Clubs URLs
        cursor.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE url LIKE '%www.athle.fr%') as new_format,
                COUNT(*) FILTER (WHERE url LIKE '%bases.athle.fr%') as old_format,
                COUNT(*) FILTER (WHERE url IS NULL OR url = '') as missing
            FROM clubs
        """
        )
        club_urls = cursor.fetchone()
        url_stats["clubs"] = {
            "new_format": club_urls[0],
            "old_format": club_urls[1],
            "missing": club_urls[2],
        }

        return url_stats

    except Exception as e:
        logger.error(f"Error analyzing URLs: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()


def print_report():
    """Affiche un rapport complet d'analyse."""
    print("\n" + "=" * 80)
    print(" ANALYSE DE LA BASE DE DONNÉES - BASES ATHLÉ")
    print("=" * 80 + "\n")

    # Statistiques générales
    print("📊 STATISTIQUES GÉNÉRALES")
    print("-" * 80)
    stats = get_table_stats()
    if stats:
        if "athletes" in stats:
            print("\nAthlètes:")
            print(f"  Total                    : {stats['athletes']['total']:,}")
            print(f"  Avec license_id valide   : {stats['athletes']['with_valid_license']:,}")
            print(f"  Sans license_id          : {stats['athletes']['without_license']:,}")
            print(f"  Hommes                   : {stats['athletes']['male']:,}")
            print(f"  Femmes                   : {stats['athletes']['female']:,}")
            if stats["athletes"]["oldest_year"] and stats["athletes"]["youngest_year"]:
                print(
                    f"  Années de naissance      : {stats['athletes']['oldest_year']} - {stats['athletes']['youngest_year']}"
                )

        if "clubs" in stats:
            print("\nClubs:")
            print(f"  Total                    : {stats['clubs']['total']:,}")
            if stats["clubs"]["earliest_year"] and stats["clubs"]["latest_year"]:
                print(
                    f"  Années d'activité        : {stats['clubs']['earliest_year']} - {stats['clubs']['latest_year']}"
                )
            if stats["clubs"]["avg_years_active"]:
                print(f"  Durée moyenne d'activité : {stats['clubs']['avg_years_active']:.1f} ans")

    # Qualité des données
    print("\n\n📈 QUALITÉ DES DONNÉES")
    print("-" * 80)
    quality = analyze_data_quality()

    if quality and "athletes" in quality:
        print("\nAthlètes (complétude des champs):")
        comp = quality["athletes"]["completeness"]
        print(f"  license_id   : {comp['license_id']:>5.1f}%")
        print(f"  birth_date   : {comp['birth_date']:>5.1f}%")
        print(f"  sexe         : {comp['sexe']:>5.1f}%")
        print(f"  nationality  : {comp['nationality']:>5.1f}%")
        print(f"  url          : {comp['url']:>5.1f}%")

        if quality["athletes"]["potential_duplicates"] > 0:
            print(f"\n⚠️  Doublons potentiels     : {quality['athletes']['potential_duplicates']:,}")

    if quality and "clubs" in quality:
        print("\nClubs (complétude des champs):")
        comp = quality["clubs"]["completeness"]
        print(f"  first_year   : {comp['first_year']:>5.1f}%")
        print(f"  last_year    : {comp['last_year']:>5.1f}%")
        print(f"  url          : {comp['url']:>5.1f}%")
        print(f"\n✓ Clubs actifs récemment    : {quality['clubs']['active_recently']:,}")

    # Analyse des URLs
    print("\n\n🔗 ANALYSE DES URLs")
    print("-" * 80)
    url_stats = analyze_urls()

    if url_stats and "athletes" in url_stats:
        print("\nAthlètes:")
        total_urls = sum(url_stats["athletes"].values())
        if total_urls > 0:
            print(
                f"  Nouveau format : {url_stats['athletes']['new_format']:,} ({100*url_stats['athletes']['new_format']/total_urls:.1f}%)"
            )
            print(
                f"  Ancien format  : {url_stats['athletes']['old_format']:,} ({100*url_stats['athletes']['old_format']/total_urls:.1f}%)"
            )
            print(
                f"  Manquantes     : {url_stats['athletes']['missing']:,} ({100*url_stats['athletes']['missing']/total_urls:.1f}%)"
            )

    if url_stats and "clubs" in url_stats:
        print("\nClubs:")
        total_urls = sum(url_stats["clubs"].values())
        if total_urls > 0:
            print(
                f"  Nouveau format : {url_stats['clubs']['new_format']:,} ({100*url_stats['clubs']['new_format']/total_urls:.1f}%)"
            )
            print(
                f"  Ancien format  : {url_stats['clubs']['old_format']:,} ({100*url_stats['clubs']['old_format']/total_urls:.1f}%)"
            )
            print(
                f"  Manquantes     : {url_stats['clubs']['missing']:,} ({100*url_stats['clubs']['missing']/total_urls:.1f}%)"
            )

    # Recommandations
    print("\n\n💡 RECOMMANDATIONS")
    print("-" * 80)

    recommendations = []

    if url_stats and "athletes" in url_stats:
        if url_stats["athletes"]["old_format"] > 0:
            recommendations.append(
                f"⚠️  {url_stats['athletes']['old_format']:,} athlètes avec anciennes URLs à mettre à jour"
            )

    if quality and "athletes" in quality:
        if quality["athletes"]["completeness"]["license_id"] < 90:
            recommendations.append(
                f"⚠️  {100 - quality['athletes']['completeness']['license_id']:.1f}% des athlètes sans license_id valide"
            )

        if quality["athletes"]["potential_duplicates"] > 0:
            recommendations.append(
                f"⚠️  {quality['athletes']['potential_duplicates']:,} doublons potentiels à vérifier"
            )

    if recommendations:
        for rec in recommendations:
            print(f"  {rec}")
    else:
        print("  ✓ Pas de problème détecté")

    print("\n" + "=" * 80 + "\n")


def main():
    """Fonction principale"""
    setup_logging("analyze_database")

    try:
        print_report()
    except DatabaseConnectionError as e:
        logger.error(f"Erreur de connexion: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
