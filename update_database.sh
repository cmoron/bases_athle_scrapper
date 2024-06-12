#!/bin/bash

# Définir les variables
SCRIPTS_DIR="$(dirname "$(readlink -f "$0")")"
CURRENT_YEAR="$(date +"%Y")"

# Exécuter les scripts de mise à jour
cd "${SCRIPTS_DIR}"
./list-clubs.py
if [ $? -ne 0 ]; then
    echo "Échec de l'exécution de list-clubs.py"
    exit 1
fi

./list-athletes.py --first-year "${CURRENT_YEAR}"
if [ $? -ne 0 ]; then
    echo "Échec de l'exécution de list-athletes.py"
    exit 1
fi

echo "Mise à jour réussie"
