#!/bin/bash
#
# Script de mise à jour de la base de données Bases Athlé
# Mise à jour automatique des clubs et athlètes pour la saison en cours
#

set -e  # Arrêter en cas d'erreur

# Déterminer la saison en cours (septembre = début nouvelle saison)
CURRENT_YEAR="$(date +"%Y")"
CURRENT_MONTH="$(date +"%m")"

if [ "$CURRENT_MONTH" -ge 9 ]; then
    SEASON=$((CURRENT_YEAR + 1))
else
    SEASON="$CURRENT_YEAR"
fi

echo "================================================================================"
echo "🚀 Mise à jour de la base Athlé - Saison ${SEASON}"
echo "================================================================================"
echo ""

# Vérifier que Python est disponible
if ! command -v python3 &> /dev/null; then
    echo "❌ Erreur: python3 n'est pas installé"
    exit 1
fi

# Mise à jour des clubs
echo "📥 Mise à jour des clubs..."
if python3 -m scraper.list_clubs --first-year "${SEASON}"; then
    echo "✅ Mise à jour des clubs réussie"
else
    echo "❌ Échec de la mise à jour des clubs"
    exit 1
fi
echo ""

# Mise à jour des athlètes
echo "🏃 Mise à jour des athlètes pour la saison ${SEASON}..."
if python3 -m scraper.list_athletes --first-year "${SEASON}"; then
    echo "✅ Mise à jour des athlètes réussie"
else
    echo "❌ Échec de la mise à jour des athlètes"
    exit 1
fi
echo ""

echo "================================================================================"
echo "✅ Mise à jour terminée avec succès !"
echo "================================================================================"
echo ""
echo "📊 Pour voir les statistiques, lancez:"
echo "   python3 -m tools.analyze_database"
echo ""
