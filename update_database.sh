#!/bin/bash

set -e

CURRENT_YEAR="$(date +"%Y")"
CURRENT_MONTH="$(date +"%m")"

if [ "$CURRENT_MONTH" -ge 9 ]; then
    SEASON=$((CURRENT_YEAR + 1))
else
    SEASON="$CURRENT_YEAR"
fi

echo "🚀 Mise à jour de la base athlé - Saison ${SEASON}"
echo "📥 Mise à jour des clubs..."
python list_clubs.py

echo "🏃 Mise à jour des athlètes pour la saison ${SEASON}..."
python list_athletes.py --first-year "${SEASON}"

echo "✅ Mise à jour terminée avec succès !"
