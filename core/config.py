"""Configuration for logging in the scraping project."""
import logging
import sys
import os
from datetime import datetime
from pathlib import Path
import shutil

# Répertoires de logs (à la racine du projet, pas dans core/)
LOG_DIR = Path(__file__).parent.parent / 'logs'
ARCHIVE_DIR = LOG_DIR / 'archive'

def setup_logging(
    script_name='scraping',
    console_level=logging.INFO,
    file_level=logging.DEBUG
):
    """
    Configure le logging pour l'application avec rotation automatique.

    Args:
        script_name: Nom du script (pour le fichier de log)
        console_level: Niveau de log pour la console
        file_level: Niveau de log pour le fichier

    Returns:
        Logger configuré
    """
    # Créer les répertoires si nécessaires
    LOG_DIR.mkdir(exist_ok=True)
    ARCHIVE_DIR.mkdir(exist_ok=True)

    # Nom du fichier de log avec timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f"{script_name}_{timestamp}.log"
    log_path = LOG_DIR / log_filename

    # Archiver l'ancien log s'il existe
    archive_old_logs(script_name)

    # Configuration du root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Nettoyer les handlers existants (important pour éviter les doublons)
    root_logger.handlers.clear()

    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler fichier
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)

    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)

    # Ajouter les handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Limiter les logs des bibliothèques tierces
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('psycopg2').setLevel(logging.WARNING)

    # Logger le démarrage
    root_logger.info("=" * 80)
    root_logger.info(f"Démarrage du script: {script_name}")
    root_logger.info(f"Fichier de log: {log_path}")
    root_logger.info("=" * 80)

    return root_logger

def archive_old_logs(script_name, keep_last=5):
    """
    Archive les anciens logs d'un script donné.

    Args:
        script_name: Nom du script
        keep_last: Nombre de logs à garder dans le répertoire principal
    """
    # Trouver tous les logs de ce script
    pattern = f"{script_name}_*.log"
    log_files = sorted(LOG_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)

    # Garder les N plus récents, archiver les autres
    for old_log in log_files[keep_last:]:
        archive_path = ARCHIVE_DIR / old_log.name
        try:
            shutil.move(str(old_log), str(archive_path))
            logging.debug(f"Archived old log: {old_log.name}")
        except Exception as e:
            logging.warning(f"Failed to archive {old_log.name}: {e}")

def cleanup_old_archives(days=30):
    """
    Supprime les logs archivés de plus de N jours.

    Args:
        days: Nombre de jours à garder
    """
    import time

    cutoff_time = time.time() - (days * 86400)

    for archive_file in ARCHIVE_DIR.glob('*.log'):
        if archive_file.stat().st_mtime < cutoff_time:
            try:
                archive_file.unlink()
                logging.debug(f"Deleted old archive: {archive_file.name}")
            except Exception as e:
                logging.warning(f"Failed to delete {archive_file.name}: {e}")

def get_logger(name):
    """
    Retourne un logger pour un module spécifique.

    Args:
        name: Nom du module (__name__ généralement)

    Returns:
        Logger configuré
    """
    return logging.getLogger(name)
