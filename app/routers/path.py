from fastapi import APIRouter, HTTPException
from app.models.schemas import PathRequest, AnalysisResponse, DijkstraPathRequest, AllShortestPathsRequest
from app.services.path_service import PathService

router = APIRouter()
service = PathService()

@router.post("/shortest", response_model=AnalysisResponse)
async def get_shortest_path(request: PathRequest):
    """Find the shortest path"""
    try:
        result = service.find_shortest_path(
            request.start_node_id,
            request.end_node_id,
            request.relationship_type,
            request.max_hops
        )
        return AnalysisResponse(
            success=True,
            data=result,
            metadata={
                "algorithm": "cypher_shortest_path",
                "weighted": False
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/all", response_model=AnalysisResponse)
async def get_all_paths(request: PathRequest):
    """Find all paths"""
    try:
        result = service.find_all_paths(
            request.start_node_id,
            request.end_node_id,
            request.relationship_type,
            request.max_hops
        )
        return AnalysisResponse(
            success=True,
            data=result,
            metadata={
                "algorithm": "cypher_all_paths",
                "max_results": 100
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/shortest-dijkstra", response_model=AnalysisResponse)
async def get_shortest_path_dijkstra(request: DijkstraPathRequest):
    """
    Find the shortest path using Dijkstra’s algorithm (GDS)

    Advantages:
        - Supports relationship weights
        - More efficient on large graphs
        - Returns the total path cost

        Options:
        - relationshipWeightProperty: name of the property containing the weight
          (if absent, all relationships have a weight of 1)
        - graph_name: name of the temporary graph (auto-generated if not provided)

        Example with weights:
        ```
        // In Neo4j, create relationships with weights:
        CREATE (a:City {name: 'Paris'})-[:ROUTE {distance: 350}]->(b:City {name: 'Lyon'})

        // Call the API:
        {
          "start_node_id": 123,
          "end_node_id": 456,
          "relationship_type": "ROUTE",
          "options": {
            "relationshipWeightProperty": "distance"
          }
        }
        ```
    """
    try:
        result = service.find_shortest_path_dijkstra(
            request.start_node_id,
            request.end_node_id,
            request.relationship_type,
            request.options
        )
        return AnalysisResponse(
            success=True,
            data=result,
            metadata={
                "algorithm": "dijkstra",
                "weighted": request.options.get("relationshipWeightProperty") is not None,
                "weight_property": request.options.get("relationshipWeightProperty", "none")
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/all-shortest-dijkstra", response_model=AnalysisResponse)
async def get_all_shortest_paths_dijkstra(request: AllShortestPathsRequest):
    """
    Find all shortest paths from a source node (SSSP)

    Calculates the shortest path from the source node to ALL other nodes.
    Useful for:
    - Calculating distances from a central point
    - Finding the most accessible nodes
    - Distance-based centrality analysis

    Options:
    - relationshipWeightProperty: weight property
    - max_distance: maximum distance (filters the results)
    """
    try:
        result = service.find_all_shortest_paths_dijkstra(
            request.start_node_id,
            request.relationship_type,
            request.options
        )
        return AnalysisResponse(
            success=True,
            data=result,
            metadata={
                "algorithm": "dijkstra_sssp",
                "source_node": request.start_node_id,
                "paths_found": len(result)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

