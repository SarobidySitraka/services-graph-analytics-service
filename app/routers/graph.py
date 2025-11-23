from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import (
    AnalysisResponse, NodeSearchRequest, NeighborsRequest,
    SubgraphRequest, ConnectionCheckRequest
)
from app.services.neo4j_service import Neo4jService

router = APIRouter()
service = Neo4jService()


@router.get("/stats", response_model=AnalysisResponse)
async def get_graph_statistics():
    """
    Retrieve global graph statistics

    Returns:
    - Total number of nodes
    - Total number of relationships
    - List of node labels
    - List of relationship types
    """
    try:
        result = service.get_graph_stats()
        return AnalysisResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/detailed", response_model=AnalysisResponse)
async def get_detailed_statistics():
    """
    Retrieve detailed graph statistics

    Returns:
    - Node distribution by label
    - Relationship distribution by type
    - Degree statistics (average, min, max, standard deviation)
    """
    try:
        result = service.get_detailed_stats()
        return AnalysisResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/node/{node_id}", response_model=AnalysisResponse)
async def get_node(node_id: int):
    """
    Retrieve a node by its ID

    Returns:
    - Node ID
    - Labels
    - All properties
    """
    try:
        result = service.get_node_by_id(node_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        return AnalysisResponse(success=True, data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/node/{node_id}/relationships", response_model=AnalysisResponse)
async def get_node_with_relationships(
        node_id: int,
        limit: int = Query(default=50, le=500)
):
    """
    Retrieve a node with all its relationships

    Returns:
    - Node information
    - Outgoing relationships
    - Incoming relationships
    - Counters
    """
    try:
        result = service.get_node_with_relationships(node_id, limit)
        if not result:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        return AnalysisResponse(success=True, data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=AnalysisResponse)
async def search_nodes(request: NodeSearchRequest):
    """
    Search for nodes by label and/or properties

    Examples:
    - All Person nodes: {"label": "Person"}
    - People aged 30: {"label": "Person", "property_filters": {"age": 30}}
    - All cities named Paris: {"property_filters": {"name": "Paris"}}
    """
    try:
        result = service.search_nodes(
            request.label,
            request.property_filters,
            request.limit
        )
        return AnalysisResponse(
            success=True,
            data=result,
            metadata={"count": len(result)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/neighbors", response_model=AnalysisResponse)
async def get_neighbors(request: NeighborsRequest):
    """
    Retrieve a node’s neighbors

    Options:
    - direction: "OUTGOING", "INCOMING", or "BOTH"
    - relationship_type: filter by relationship type (optional)
    - limit: maximum number of neighbors

    Examples:
    - All friends: {"node_id": 123, "relationship_type": "FRIEND", "direction": "BOTH"}
    - Followers: {"node_id": 123, "relationship_type": "FOLLOWS", "direction": "INCOMING"}
    - Following: {"node_id": 123, "relationship_type": "FOLLOWS", "direction": "OUTGOING"}
    """
    try:
        result = service.get_neighbors(
            request.node_id,
            request.relationship_type,
            request.direction,
            request.limit
        )
        return AnalysisResponse(
            success=True,
            data=result,
            metadata={
                "node_id": request.node_id,
                "neighbors_count": len(result),
                "direction": request.direction
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subgraph", response_model=AnalysisResponse)
async def get_subgraph(request: SubgraphRequest):
    """
    Retrieve a subgraph from a list of node IDs

    Returns:
    - All requested nodes with their properties
    - All relationships between these nodes

    Useful for:
    - Visualizing part of the graph
    - Exporting a graph subset
    - Analyzing connections within a group of nodes

    Limit: max 1000 nodes
    """
    try:
        result = service.get_subgraph(request.node_ids)
        return AnalysisResponse(
            success=True,
            data=result,
            metadata={
                "requested_nodes": len(request.node_ids),
                "returned_nodes": len(result.get("nodes", [])),
                "relationships": len(result.get("relationships", []))
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-connection", response_model=AnalysisResponse)
async def check_connection(request: ConnectionCheckRequest):
    """
    Check if two nodes are connected

    Returns True/False depending on whether a path exists between the two nodes

    Options:
    - relationship_type: type of relationship to consider (optional)
    - max_hops: maximum search depth (default: 5)

    Faster than find_shortest_path because it stops as soon as a connection is found
    """
    try:
        result = service.check_connection_exists(
            request.start_node_id,
            request.end_node_id,
            request.relationship_type,
            request.max_hops
        )
        return AnalysisResponse(
            success=True,
            data={"connected": result},
            metadata={
                "start_node_id": request.start_node_id,
                "end_node_id": request.end_node_id,
                "max_hops": request.max_hops
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/info", response_model=AnalysisResponse)
async def get_database_info():
    """
    Retrieve Neo4j database information

    Returns:
    - Neo4j version
    - Edition (Community/Enterprise)
    - List of constraints
    - List of indexes

    Useful for:
    - Diagnosing configuration
    - Checking available indexes
    - Security auditing
    """
    try:
        result = service.get_database_info()
        return AnalysisResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))