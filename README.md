# Bases Athlé Scraper 🏃

[![CI](https://github.com/cmoron/bases_athle_scrapper/actions/workflows/ci.yml/badge.svg)](https://github.com/cmoron/bases_athle_scrapper/actions/workflows/ci.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=cmoron_bases_athle_scrapper&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=cmoron_bases_athle_scrapper)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=cmoron_bases_athle_scrapper&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=cmoron_bases_athle_scrapper)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=cmoron_bases_athle_scrapper&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=cmoron_bases_athle_scrapper)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=cmoron_bases_athle_scrapper&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=cmoron_bases_athle_scrapper)
[![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=cmoron_bases_athle_scrapper&metric=code_smells)](https://sonarcloud.io/summary/new_code?id=cmoron_bases_athle_scrapper)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

Scraper des données d'athlétisme de la FFA (Fédération Française d'Athlétisme) depuis [bases.athle.fr](https://www.athle.fr/bases/).

## 🚀 Installation

### Prérequis
- Python 3.12+
- PostgreSQL 16
- Docker (pour les tests)

### Installation des dépendances

```bash
# Production
pip install -r requirements.txt

# Développement (inclut tests + qualimétrie)
pip install -r requirements-dev.txt
```

### Configuration

Créer un fichier `.env` à la racine :

```bash
POSTGRES_DEFAULT_DB=postgres
POSTGRES_DB=athle
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

## 📊 Usage

### Peuplement initial de la base de données (2004-2025)

```bash
./populate_database.sh
```

⚠️ Cette opération peut prendre plusieurs heures.

### Mise à jour régulière (saison en cours uniquement)

```bash
./update_database.sh
```

### Analyse de la base de données

```bash
python3 -m tools.analyze_database
```

## 🧪 Tests

```bash
# Lancer tous les tests
make test

# Tests avec coverage
make coverage

# Voir le rapport HTML
open htmlcov/index.html
```

**Couverture actuelle** : ~54% (objectif : 80%)

## 🔍 Qualimétrie

Le projet utilise une stack moderne de qualimétrie :

```bash
# Formater le code automatiquement
make format

# Vérifier la qualité (linter + type checking)
make lint

# Simuler la CI en local
make ci
```

### Outils utilisés

- **black** : Formatage automatique du code
- **ruff** : Linter ultra-rapide (remplace flake8, isort, pylint)
- **mypy** : Type checking statique
- **pytest** + **pytest-cov** : Tests et coverage
- **testcontainers** : Tests d'intégration avec PostgreSQL

## 🛠️ Développement

### Structure du projet

```
.
├── core/                 # Configuration, DB, schéma
│   ├── config.py         # Logging et configuration
│   ├── db.py             # Connexions PostgreSQL
│   └── schema.sql        # Schéma complet (tables, index, triggers)
├── scraper/              # Scrapers
│   ├── list_clubs.py     # Scraper des clubs
│   └── list_athletes.py  # Scraper des athlètes
├── tools/                # Outils d'analyse
│   └── analyze_database.py
├── tests/                # Tests unitaires (pytest + testcontainers)
└── logs/                 # Logs d'exécution
```

### Commandes Make disponibles

```bash
make help              # Liste toutes les commandes
make install           # Installe les dépendances dev
make test              # Lance les tests
make coverage          # Tests + rapport coverage HTML
make lint              # Vérifie la qualité (ruff + mypy)
make format            # Formate le code (black + ruff)
make check             # Lint + tests
make ci                # Simule la CI en local
make clean             # Nettoie les fichiers temporaires
```

## 🐳 Docker

### Lancer PostgreSQL

```bash
docker-compose up -d postgres
```

### Lancer le scraper dockerisé

```bash
docker-compose up scraper
```

Les logs sont persistés dans `./logs/` sur l'host.

## 📈 CI/CD

Le projet utilise **GitHub Actions** pour :
- ✅ Vérifier le formatage (black)
- ✅ Linter le code (ruff)
- ✅ Type checking (mypy)
- ✅ Lancer les tests avec PostgreSQL
- ✅ Générer un rapport de coverage

Voir [.github/workflows/ci.yml](.github/workflows/ci.yml)

## 📝 Schéma de base de données

### Tables principales

#### `clubs`
- `id` : SERIAL PRIMARY KEY (auto-généré)
- `ffa_id` : TEXT NOT NULL UNIQUE (identifiant FFA)
- `name` : TEXT NOT NULL
- `normalized_name` : TEXT NOT NULL (pour recherche floue)
- `first_year`, `last_year` : INTEGER (période d'activité)
- `created_at`, `updated_at` : TIMESTAMP

#### `athletes`
- `id` : SERIAL PRIMARY KEY (auto-généré)
- `ffa_id` : TEXT NOT NULL UNIQUE (identifiant FFA)
- `license_id` : TEXT (numéro de licence, unique si valide)
- `name` : TEXT NOT NULL
- `normalized_name` : TEXT NOT NULL
- `birth_date`, `sexe`, `nationality` : TEXT
- `created_at`, `updated_at` : TIMESTAMP

### Fonctionnalités PostgreSQL

- **Triggers** : Mise à jour automatique de `normalized_name` et `updated_at`
- **Extensions** : `pg_trgm` (recherche floue), `unaccent` (normalisation)
- **Index GIN** : Recherche trigram sur les noms
- **Index partiel** : Unicité conditionnelle sur `license_id`

## 🤝 Contribution

1. Fork le projet
2. Crée une branche (`git checkout -b feature/amazing-feature`)
3. Formate ton code (`make format`)
4. Vérifie la qualité (`make check`)
5. Commit tes changements
6. Push et ouvre une Pull Request

## 📄 Licence

Ce projet est sous licence MIT.
