from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import centrality, community, anomaly, path, prediction, graph

app = FastAPI(
    title=settings.app_name,
    description="Graph analysis service with neo4j",
    version="0.1.0",
    debug=settings.debug
)

# CORS middleware
origins = [
	"http://localhost:3000",
	"http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.app_name}


@app.get("/")
async def root():
    return {
        "message": "GraphAnalysis API",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "centrality": "/api/centrality/*",
            "community": "/api/community/*",
            "anomaly": "/api/anomaly/*",
            "path": "/api/path/*",
            "prediction": "/api/prediction/*",
            "graph": "/api/graph/*"
        }
    }

# Include routers
app.include_router(centrality.router, prefix="/api/centrality", tags=["Centrality"])
app.include_router(community.router, prefix="/api/community", tags=["Community"])
app.include_router(anomaly.router, prefix="/api/anomaly", tags=["Anomaly"])
app.include_router(path.router, prefix="/api/path", tags=["Pathfinding"])
app.include_router(prediction.router, prefix="/api/prediction", tags=["Prediction"])
app.include_router(graph.router, prefix="/api/graph", tags=["Graph Operations"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)