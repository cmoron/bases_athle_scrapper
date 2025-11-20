#!/bin/bash
#
# Script de peuplement initial de la base de données Bases Athlé
# Récupère toutes les données depuis 2004 jusqu'à aujourd'hui
#

set -e  # Arrêter en cas d'erreur

FIRST_YEAR=2004

# Déterminer la saison actuelle (septembre = début nouvelle saison)
CURRENT_YEAR="$(date +"%Y")"
CURRENT_MONTH="$(date +"%m")"

if [ "$CURRENT_MONTH" -ge 9 ]; then
    LAST_YEAR=$((CURRENT_YEAR + 1))
else
    LAST_YEAR="$CURRENT_YEAR"
fi

echo "================================================================================"
echo "🚀 Peuplement initial de la base Athlé"
echo "📅 Période: ${FIRST_YEAR} - ${LAST_YEAR}"
echo "================================================================================"
echo ""
echo "⚠️  ATTENTION: Cette opération peut prendre plusieurs heures"
echo "   - Clubs: Environ 5-10 minutes"
echo "   - Athlètes: Plusieurs heures selon le nombre de clubs et d'années"
echo ""

# Étape 1: Récupération de tous les clubs
echo "================================================================================"
echo "📥 ÉTAPE 1/2: Récupération des clubs (${FIRST_YEAR} - ${LAST_YEAR})"
echo "================================================================================"
START_TIME=$(date +%s)

if python3 -m scraper.list_clubs --first-year "${FIRST_YEAR}"; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    echo "✅ Récupération des clubs terminée en ${DURATION}s"
else
    echo "❌ Échec de la récupération des clubs"
    exit 1
fi
echo ""

# Étape 2: Récupération de tous les athlètes
echo "================================================================================"
echo "🏃 ÉTAPE 2/2: Récupération des athlètes (${FIRST_YEAR} - ${LAST_YEAR})"
echo "================================================================================"
echo "⏳ Cette étape peut prendre plusieurs heures..."
START_TIME=$(date +%s)

if python3 -m scraper.list_athletes --first-year "${FIRST_YEAR}" --last-year "${LAST_YEAR}"; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    HOURS=$((DURATION / 3600))
    MINUTES=$(((DURATION % 3600) / 60))
    SECONDS=$((DURATION % 60))
    echo "✅ Récupération des athlètes terminée en ${HOURS}h ${MINUTES}m ${SECONDS}s"
else
    echo "❌ Échec de la récupération des athlètes"
    exit 1
fi
echo ""

echo "================================================================================"
echo "✅ Peuplement initial terminé avec succès !"
echo "================================================================================"
echo ""
echo "📊 Pour voir les statistiques de la base de données, lancez:"
echo "   python3 -m tools.analyze_database"
echo ""
echo "💡 Pour les mises à jour futures (saison en cours uniquement), utilisez:"
echo "   ./update_database.sh"
echo ""
