#!/bin/bash

echo "Initialisation du projet GraphAnalysis"

# Vérifier si uv est installé
if ! command -v uv &> /dev/null; then
    echo "uv n'est pas installé"
    echo "Installation de uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "uv installé"
fi

# Créer le fichier .env s'il n'existe pas
if [ ! -f .env ]; then
    echo "Création du fichier .env"
    cp .env.example .env
fi

# Créer le lock file
echo "Génération du uv.lock"
uv lock

# Synchroniser l'environnement local
echo "Installation des dépendances"
uv sync

echo "Projet initialisé avec succès!"
echo ""
echo "Pour démarrer:"
echo "  - Mode développement: ./dev.sh ou docker compose watch"
echo "  - Mode production: ./run.sh ou docker compose up"
echo "  - Local (sans Docker): uv run uvicorn app.main:app --reload"
