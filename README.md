# GraphAnalysis Service

Service d'analyse de graphe basé sur FastAPI et Neo4j avec support APOC.

Utilise [uv](https://docs.astral.sh/uv/) pour une gestion rapide et moderne des dépendances Python.

## Fonctionnalités

- **Centralité** : Betweenness, Closeness, Degree, PageRank
- **Détection de Communautés** : Louvain, Greedy, WCC
- **Détection d'Anomalies** : Outliers
- **Pathfinding** : Chemin le plus court, tous les chemins
- **Prédiction** : Link prediction, Node property prediction

## Prérequis

- Docker et Docker Compose (pour le déploiement conteneurisé)
- [uv](https://docs.astral.sh/uv/) (pour le développement local)

## Installation

### Setup rapide

```bash
# Clone et initialisation automatique
git clone <repo>
cd graph-analysis-service
chmod +x setup.sh && ./setup.sh
```

### Setup manuel

```bash
# Installer uv (si nécessaire)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Créer le fichier .env
cp .env.example .env

# Générer le lock file et installer les dépendances
uv lock
uv sync
```

## Démarrage rapide

### Avec Docker (Recommandé)

```bash
# Mode production
docker compose up --build -d

# Mode développement avec hot-reload
docker compose watch
```

L'API sera disponible à `http://localhost:8000`
Neo4j à `http://localhost:7474`

### Sans Docker (Développement local)

```bash
# Démarrer Neo4j (via Docker ou localement)
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.15

# Lancer l'API avec uv
uv run uvicorn app.main:app --reload
```

## Endpoints

### Centralité
- `POST /api/centrality/betweenness`
- `POST /api/centrality/closeness`
- `POST /api/centrality/degree`
- `POST /api/centrality/pagerank`

### Communautés
- `POST /api/community/louvain`
- `POST /api/community/greedy`
- `POST /api/community/wcc`

### Anomalies
- `POST /api/anomaly/detect`

### Pathfinding
- `POST /api/path/shortest`
- `POST /api/path/all`

### Prédiction
- `POST /api/prediction/links`
- `POST /api/prediction/node-properties`

## Exemple d'utilisation

```bash
curl -X POST "http://localhost:8000/api/centrality/pagerank" \
  -H "Content-Type: application/json" \
  -d '{
    "relationship_type": "RELATED",
    "algorithm": "pagerank",
    "options": {"iterations": 20}
  }'
```

## Documentation Interactive

Swagger UI : `http://localhost:8000/docs`
ReDoc : `http://localhost:8000/redoc`

## Architecture

- **main.py** : Point d'entrée FastAPI
- **config.py** : Configuration de l'application
- **database.py** : Gestion de la connexion Neo4j
- **services/** : Logique métier pour chaque type d'analyse
- **routers/** : Endpoints API
- **models/schemas.py** : Schémas de validation Pydantic

## Améliorations futures

- [ ] Caching des résultats
- [ ] Authentification/Autorisation
- [ ] Pagination des résultats
- [ ] Endpoints de gestion du graphe
- [ ] Monitoring et logs structurés
- [ ] Tests unitaires
- [ ] Support des transactions
- [ ] Validation des entrées améliorée