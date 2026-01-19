#!/bin/bash

# Construire et lancer les services
docker compose up --build -d

echo "Services démarrés"
echo "  - API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Neo4j: http://localhost:7474"
