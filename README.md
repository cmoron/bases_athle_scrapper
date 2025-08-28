# Athletics Data Extraction

Ce projet contient deux scripts Python qui extraient des informations sur les clubs et les athlètes d'athlétisme depuis le site de la Fédération Française d'Athlétisme et les stockent dans une base de données PostgreSQL.

## Structure du Projet

- `list_clubs.py` : Script pour extraire les informations des clubs d'athlétisme et les stocker dans une base de données PostgreSQL.
- `list_athletes.py` : Script pour extraire les informations des athlètes à partir des clubs enregistrés et les stocker également dans la base de données PostgreSQL.

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

## Utilisation

### Extraction des Clubs

Pour lancer l'extraction des clubs :

```bash
python list_clubs.py
```

### Extraction des Athlètes

Avant d'exécuter le script d'extraction des athlètes, assurez-vous que la base de données contenant les clubs est disponible et correctement remplie. Ensuite, exécutez :

```bash
python list_athletes.py
```

## Fonctionnalités

- Extraction automatique des données des clubs et des athlètes pour différentes années.
- Stockage des données dans une base de données PostgreSQL pour un accès facile et rapide.
- Gestion des erreurs de réseau pour garantir la robustesse des scripts.

## Contribution

Les contributions à ce projet sont les bienvenues. Vous pouvez proposer des améliorations ou des corrections en soumettant des pull requests ou des issues sur le dépôt GitHub.

## Licence

Ce projet est distribué sous la licence MIT. Voir le fichier LICENSE pour plus de détails.
