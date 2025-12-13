# Refactorisation du projet Bases Athlé

## 📋 Contexte

Suite aux changements majeurs du site bases.athle.fr :
- Nouvelles URLs pour les pages athlètes et clubs
- Changement des IDs athlètes (overlaps possibles entre anciens et nouveaux IDs)
- Nouveau format HTML

**Décision** : Refactorisation complète avec nouvelle architecture de base de données.

---

## 🎯 Objectifs de la refactorisation

1. ✅ **IDs internes auto-générés** - Plus de conflits possibles
2. ✅ **`license_id` comme clé métier** - Identifiant stable et fiable
3. ✅ **`normalized_name` pour recherche performante** - Index trigram pour recherches floues rapides
4. ✅ **Gestion des logs améliorée** - Rotation automatique et archivage
5. ✅ **Architecture modulaire** - Code organisé en modules (scraper/, tools/)

---

## 🏗️ Nouvelle architecture

```
mypacer_scraper/
├── core/                       # ✅ Module fondamental
│   ├── __init__.py
│   ├── db.py                   # ✅ Connexion base de données
│   ├── config.py               # ✅ Configuration logs améliorée
│   ├── schema.py               # ✅ Gestion du schéma
│   └── schema.sql              # ✅ Définition du schéma SQL
├── scraper/                    # Module de scraping
│   ├── __init__.py
│   ├── list_athletes.py        # Script de scraping athlètes
│   └── list_clubs.py           # Script de scraping clubs
├── tools/                      # Outils d'analyse et maintenance
│   ├── __init__.py
│   └── analyze_database.py     # ✅ Script d'analyse consolidé
├── tests/                      # Tests unitaires
│   ├── test_duplicate_handling.py
│   └── test_storage.py
├── logs/                       # Logs avec rotation automatique
│   ├── archive/                # Anciens logs archivés
│   └── *.log                   # Logs actifs (5 derniers)
├── update_database.sh          # Script principal de mise à jour
└── README.md
```

---

## 📊 Nouveau schéma de base de données

### Table `athletes`

```sql
CREATE TABLE athletes (
    id SERIAL PRIMARY KEY,                    -- ✅ ID interne auto-increment
    ffa_id TEXT NOT NULL UNIQUE,              -- ID FFA (abstrait)
    license_id TEXT,                          -- Numéro de licence (clé métier)
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,            -- ✅ Pour recherche rapide
    url TEXT,
    birth_date TEXT,
    sexe TEXT,
    nationality TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index unique partiel : garantit qu'un license_id valide ne peut exister qu'une fois
CREATE UNIQUE INDEX idx_athletes_license_id_unique ON athletes(license_id)
    WHERE license_id IS NOT NULL
      AND license_id != ''
      AND license_id != '-'
      AND license_id != 'None';
```

**Index créés** :
- `idx_athletes_ffa_id` - Recherche par ID FFA
- `idx_athletes_license_id_unique` - ✅ **Index unique partiel** sur license_id (exclut valeurs invalides)
- `idx_athletes_normalized_name_trgm` - Recherche floue ultra-rapide (GIN trigram)
- `idx_athletes_license_id` - Recherche par numéro de licence
- Autres index sur sexe, birth_date, etc.

### Table `clubs`

```sql
CREATE TABLE clubs (
    id SERIAL PRIMARY KEY,
    ffa_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    first_year INTEGER,
    last_year INTEGER,
    url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Triggers automatiques

- `trigger_update_athlete_normalized_name` - Met à jour automatiquement `normalized_name` et `updated_at`
- `trigger_update_club_normalized_name` - Idem pour clubs

### Vues utiles

- `v_athletes_stats` - Statistiques globales sur les athlètes
- `v_clubs_stats` - Statistiques globales sur les clubs

---

## 🔧 Améliorations apportées

### 1. Gestion des logs (`core/config.py`)

**Avant** :
- Un seul fichier `scrapping.log`
- Pas de rotation
- Logs qui grossissent indéfiniment

**Après** :
```python
from core.config import setup_logging
setup_logging('update_database')  # Crée update_database_20251115_174530.log
```

✅ **Fonctionnalités** :
- Nom de fichier avec timestamp
- Rotation automatique (garde les 5 derniers)
- Archivage des anciens dans `logs/archive/`
- Nettoyage automatique des archives > 30 jours

### 2. Schéma de base de données (`core/schema.sql` + `core/schema.py`)

**Avant** :
- Tables créées directement dans les scripts
- Pas de normalisation des noms
- Pas de vues ni de fonctions

**Après** :
```bash
python -m core.schema  # Crée toutes les tables + indexes + triggers + vues
```

✅ **Fonctionnalités** :
- Schéma complet en SQL
- Fonction `normalize_text()` PostgreSQL
- Triggers automatiques
- Vues pour statistiques
- Extension `pg_trgm` pour recherche rapide

### 3. Analyse de la base (`tools/analyze_database.py`)

**Avant** :
- Multiples scripts (analyze_duplicates.py, cleanup_duplicates.py, etc.)
- Analyses fragmentées

**Après** :
```bash
python tools/analyze_database.py  # Analyse complète en un seul script
```

✅ **Affiche** :
- Statistiques générales (totaux, répartition H/F, années)
- Qualité des données (complétude de chaque champ)
- Analyse des URLs (ancien/nouveau format)
- Doublons potentiels
- Recommandations

---

## 🚀 Plan de migration

### Étape 1 : Backup de l'ancienne base

```bash
# Backup complet
pg_dump -U $POSTGRES_USER -d $POSTGRES_DB > backup_before_refactoring_$(date +%Y%m%d).sql

# Ou utiliser votre script de backup
./your_backup_script.sh
```

### Étape 2 : Créer le nouveau schéma

```bash
# Option 1 : Via le script Python
python -m core.schema

# Option 2 : Directement en SQL
psql -U $POSTGRES_USER -d $POSTGRES_DB -f core/schema.sql
```

### Étape 3 : Adapter les scripts de scraping

**À faire** :
1. Déplacer `list_athletes.py` dans `scraper/`
2. Déplacer `list_clubs.py` dans `scraper/`
3. Modifier les fonctions de création de tables pour utiliser le nouveau schéma
4. Ajouter la normalisation des noms lors de l'insertion
5. Utiliser `ffa_id` au lieu de `id` pour stocker l'ID FFA

**Exemple de modification** :
```python
# AVANT
cursor.execute("""
    INSERT INTO athletes (id, name, url, birth_date, license_id, sexe, nationality)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (id) DO UPDATE ...
""", (athlete_id, name, url, birth_date, license_id, sexe, nationality))

# APRÈS
cursor.execute("""
    INSERT INTO athletes (ffa_id, name, url, birth_date, license_id, sexe, nationality)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (ffa_id) DO UPDATE ...
""", (athlete_id, name, url, birth_date, license_id, sexe, nationality))
# Note: normalized_name est géré automatiquement par le trigger
```

### Étape 4 : Mettre à jour `update_database.sh`

```bash
#!/bin/bash

LOG_FILE="logs/update.log"
TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"

# ... reste du script inchangé
```

### Étape 5 : Tester avec un petit échantillon

```bash
# Scraper quelques clubs pour tester
python scraper/list_clubs.py --first-year 2025 --last-year 2025

# Vérifier avec l'outil d'analyse
python tools/analyze_database.py
```

### Étape 6 : Migration complète (optionnelle)

Si vous voulez migrer les données existantes :

```python
# Script de migration (à créer)
# 1. Lire l'ancienne base
# 2. Insérer dans la nouvelle avec ffa_id
# 3. Laisser les triggers gérer normalized_name
```

---

## 📦 Fichiers à conserver

### ✅ Module core/ (nouveau)
- `core/db.py` - ✅ **Connexion base de données**
- `core/config.py` - ✅ **Configuration logs améliorée**
- `core/schema.py` - ✅ **Gestion du schéma**
- `core/schema.sql` - ✅ **Définition du schéma SQL**
- `core/__init__.py` - ✅ **Module package**

### ✅ Modules scraper/ et tools/
- `scraper/list_athletes.py` - ✅ **Scraping athlètes**
- `scraper/list_clubs.py` - ✅ **Scraping clubs**
- `tools/analyze_database.py` - ✅ **Script d'analyse consolidé**
- `scraper/__init__.py` - ✅ **Module package**
- `tools/__init__.py` - ✅ **Module package**

### 📝 À mettre à jour
- `update_database.sh` - À adapter pour le module core
- `README.md` - À mettre à jour

### 🗑️ À supprimer (obsolètes)
- `analyze_duplicates.py`
- `cleanup_duplicates.py`
- `analyze_id_conflicts.py`
- `update_missing_licenses.py`
- `update_old_urls.py`
- `MIGRATION_LICENSE_ID.md`

---

## 📝 Modification de l'API

Pour utiliser la recherche optimisée avec `normalized_name` :

```python
# AVANT
normalized_query = ' '.join(unidecode(name).lower().strip().split())
query_parts = normalized_query.split()
where_clause = " AND ".join(["LOWER(name) LIKE %s" for _ in query_parts])

# APRÈS
normalized_query = ' '.join(unidecode(name).lower().strip().split())
query_parts = normalized_query.split()
where_clause = " AND ".join(["normalized_name LIKE %s" for _ in query_parts])

# Bonus : tri par pertinence
query = f"""
SELECT id, ffa_id, name, url, birth_date, license_id, sexe, nationality
FROM athletes
WHERE {where_clause}
ORDER BY similarity(normalized_name, %s) DESC
LIMIT 25
"""
```

---

## ✅ Checklist de migration

- [ ] Backup de l'ancienne base effectué
- [x] **Module `core/` créé avec db, config, schema**
- [x] **Imports mis à jour dans tous les fichiers**
- [x] **`update_database.sh` mis à jour pour utiliser `python3 -m scraper.*`**
- [x] **Fichier `log.txt` hardcodé supprimé (utilise système de logging centralisé)**
- [ ] Nouveau schéma créé (`python -m core.schema`)
- [ ] Scripts de scraping adaptés pour utiliser `ffa_id`
- [ ] Tests effectués sur un petit échantillon
- [ ] API mise à jour pour utiliser `normalized_name` et `ffa_id`
- [ ] Anciens scripts obsolètes supprimés
- [ ] Documentation (`README.md`) mise à jour

---

## 🎉 Bénéfices attendus

1. **Performance** : Recherches jusqu'à 10x plus rapides avec les index trigram
2. **Robustesse** : Plus de conflits d'IDs possibles
3. **Maintenabilité** : Code organisé en modules
4. **Traçabilité** : Logs horodatés avec archivage automatique
5. **Qualité** : Indicateurs de qualité des données facilement accessibles
6. **Pérennité** : Résistant aux futurs changements du site FFA

---

## 📞 Support

Pour toute question ou problème lors de la migration :
1. Consulter les logs dans `logs/`
2. Lancer `python tools/analyze_database.py` pour diagnostiquer
3. Restaurer le backup si nécessaire
