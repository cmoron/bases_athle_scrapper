#!/bin/bash

# Définir les variables
SCRIPTS_DIR="$(dirname "$(readlink -f "$0")")"
CURRENT_YEAR="$(date +"%Y")"

# Exécuter les scripts de mise à jour
cd "${SCRIPTS_DIR}"
source "venv/bin/activate"
./list_clubs.py
if [ $? -ne 0 ]; then
    echo "Échec de l'exécution de list_clubs.py"
    exit 1
fi

./list_athletes.py --first-year "${CURRENT_YEAR}"
if [ $? -ne 0 ]; then
    echo "Échec de l'exécution de list_athletes.py"
    exit 1
fi

echo "Mise à jour réussie"
