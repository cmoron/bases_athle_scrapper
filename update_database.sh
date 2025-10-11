#!/bin/bash

LOG_FILE="update.log"
exec > >(tee -a "$LOG_FILE") 2>&1

CURRENT_YEAR="$(date +"%Y")"
CURRENT_MONTH="$(date +"%m")"

if [ "$CURRENT_MONTH" -ge 9 ]; then
    SEASON=$((CURRENT_YEAR + 1))
else
    SEASON="$CURRENT_YEAR"
fi

echo "$(date) - Début de la mise à jour (saison $SEASON)"
echo "🚀 Mise à jour de la base athlé - Saison ${SEASON}"
echo "📥 Mise à jour des clubs..."

if python list_clubs.py --first-year "${SEASON}"; then
    echo "$(date) - Mise à jour des clubs réussie"
else
    echo "$(date) - Échec de la mise à jour des clubs"
    exit 1
fi

echo "🏃 Mise à jour des athlètes pour la saison ${SEASON}..."
if python list_athletes.py --first-year "${SEASON}"; then
    echo "$(date) - Mise à jour des athlètes réussie"
else
    echo "$(date) - Échec de la mise à jour des athlètes"
    exit 1
fi

echo "✅ Mise à jour terminée avec succès !"
echo "$(date) - Fin de la mise à jour"
