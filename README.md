# Athletics Data Extraction

Ce projet fournit un package Python installable qui extrait des informations sur les clubs et les athlètes d'athlétisme depuis le site de la Fédération Française d'Athlétisme et les stocke dans une base de données.

## Structure du projet

Le code source est organisé dans un package `bases_athle_scraper` disponible sous `src/` :

- `database.py` : utilitaires de connexion à la base de données (PostgreSQL ou SQLite pour les tests).
- `clubs.py` : fonctions pour collecter et stocker les clubs.
- `athletes.py` : fonctions pour extraire et persister les athlètes.
- `cli/` : points d'entrée en ligne de commande légers.

Des scripts prêts à l'emploi sont également fournis dans le dossier `scripts/`.

## Prérequis

Vous aurez besoin de Python 3.10+ et d'une base PostgreSQL opérationnelle. Les variables suivantes peuvent être définies dans un fichier `.env` (chargé automatiquement) :

```
POSTGRES_DEFAULT_DB=postgres
POSTGRES_DB=athle
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

## Installation

Installez le package et ses dépendances en mode développement :

```bash
pip install -e .
```

Les dépendances sont également listées dans `requirements.txt` si vous préférez une installation classique.

## Utilisation

### Depuis les scripts fournis

```bash
# Extraction des clubs (toutes les saisons connues)
python scripts/scrape_clubs.py

# Extraction des athlètes (toutes les saisons, tous les clubs)
python scripts/scrape_athletes.py
```

Chaque script accepte des options supplémentaires, par exemple :

```bash
python scripts/scrape_clubs.py --first-year 2015 --last-year 2024
python scripts/scrape_athletes.py --club-id CLUB123 --update
```

### Après installation

L'installation via `pip install -e .` enregistre également deux exécutables `scrape-clubs` et `scrape-athletes` accessibles directement depuis votre shell.

## Fonctionnalités

- Extraction automatique des données des clubs et des athlètes pour différentes années.
- Stockage des données dans une base de données PostgreSQL (ou SQLite pour les tests).
- Gestion des erreurs de réseau et journalisation cohérente.

## Contribution

Les contributions à ce projet sont les bienvenues. Vous pouvez proposer des améliorations ou des corrections en soumettant des pull requests ou des issues sur le dépôt GitHub.

## Licence

Ce projet est distribué sous la licence MIT. Voir le fichier LICENSE pour plus de détails.
