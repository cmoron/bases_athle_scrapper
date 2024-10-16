#!/bin/bash

# Définir les variables
SCRIPTS_DIR="$(dirname "$(readlink -f "$0")")"
CURRENT_YEAR="$(date +"%Y")"
CURRENT_MONTH="$(date +"%m")"

# Vérifier si on est après août (mois >= 9)
if [ "$CURRENT_MONTH" -ge 9 ]; then
    SEASON=$((CURRENT_YEAR + 1))
else
    SEASON="$CURRENT_YEAR"
fi

# Exécuter les scripts de mise à jour
cd "${SCRIPTS_DIR}"
source "venv/bin/activate"
./list_clubs.py
if [ $? -ne 0 ]; then
    echo "Échec de l'exécution de list_clubs.py"
    exit 1
fi

./list_athletes.py --first-year "${SEASON}"
if [ $? -ne 0 ]; then
    echo "Échec de l'exécution de list_athletes.py"
    exit 1
fi

echo "Mise à jour réussie"
