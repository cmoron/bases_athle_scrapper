# Athletics Data Extraction

Ce projet expose un package Python dédié à l'extraction des informations sur les clubs et les athlètes d'athlétisme depuis le site de la Fédération Française d'Athlétisme et au stockage de ces données dans une base de données PostgreSQL.

## Structure du Projet

- `src/bases_athle_scrapper/` : Package Python contenant la logique métier (scraping, accès base de données, configuration du logging).
- `src/bases_athle_scrapper/cli/` : Interfaces en ligne de commande basées sur le package.
- `tests/` : Suite de tests unitaires pour vérifier le comportement du package.

## Prérequis

Pour exécuter ces scripts, vous aurez besoin de Python 3.x, d'une instance PostgreSQL en fonctionnement et des dépendances listées dans le fichier `requirements.txt`. Les paramètres de connexion à PostgreSQL doivent être définis dans un fichier `.env` :

```
POSTGRES_DEFAULT_DB=postgres
POSTGRES_DB=athle
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

## Installation

1. Clonez le dépôt GitHub ou téléchargez les fichiers du projet.
2. Installez les dépendances nécessaires :
   ```bash
   pip install -r requirements.txt
   ```
3. (Optionnel) installez le package en mode développement pour faciliter l'exécution des commandes :
   ```bash
   pip install -e .
   ```

## Utilisation

### Extraction des Clubs

Pour lancer l'extraction des clubs :

```bash
python -m bases_athle_scrapper.cli.clubs
```

### Extraction des Athlètes

Avant d'exécuter le script d'extraction des athlètes, assurez-vous que la base de données contenant les clubs est disponible et correctement remplie. Ensuite, exécutez :

```bash
python -m bases_athle_scrapper.cli.athletes
```

## Fonctionnalités

- Extraction automatique des données des clubs et des athlètes pour différentes années.
- Stockage des données dans une base de données PostgreSQL pour un accès facile et rapide.
- Gestion des erreurs de réseau pour garantir la robustesse des scripts.

## Contribution

Les contributions à ce projet sont les bienvenues. Vous pouvez proposer des améliorations ou des corrections en soumettant des pull requests ou des issues sur le dépôt GitHub.

## Licence

Ce projet est distribué sous la licence MIT. Voir le fichier LICENSE pour plus de détails.
