""" Configuration for logging in a web scraping project. """
import logging
import sys

def setup_logging(log_file='scrapping.log', console_level=logging.DEBUG, file_level=logging.DEBUG):
    """
    Configure le logging pour toute l'application.
    À appeler UNE SEULE FOIS au démarrage du programme principal.
    """
    # Configuration du root logger en WARNING (pour les libs tierces)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler fichier
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)

    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)

    # Ajouter les handlers au root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Limiter les logs des bibliothèques tierces
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

    return root_logger

def get_logger(name):
    """
    Retourne un logger pour un module spécifique.
    À utiliser dans chaque fichier.
    """
    logger = logging.getLogger(name)
    return logger
