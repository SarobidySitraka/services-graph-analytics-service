from pydantic import BaseModel, Field
from typing import Any, Optional, Literal, List

class CentralityRequest(BaseModel):
    relationship_type: str = "RELATED"
    algorithm: Literal["betweenness", "closeness", "degree", "pagerank"] = "betweenness"
    options: Optional[dict] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "relationship_type": "KNOWS",
                "algorithm": "pagerank",
                "options": {
                    "maxIterations": 20,
                    "dampingFactor": 0.85,
                    "orientation": "UNDIRECTED"
                }
            }
        }


class CommunityRequest(BaseModel):
    relationship_type: str = "RELATED"
    algorithm: Literal["louvain", "greedy", "wcc"] = "louvain"
    options: Optional[dict] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "relationship_type": "RELATED",
                "algorithm": "louvain",
                "options": {
                    "maxIterations": 10,
                    "tolerance": 0.0001,
                    "includeIntermediateCommunities": False
                }
            }
        }


class AnomalyRequest(BaseModel):
    node_label: str = "Node"
    relationship_type: Optional[str] = "RELATED"
    options: Optional[dict] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "node_label": "Person",
                "relationship_type": "KNOWS",
                "options": {
                    "method": "percentile",  # iqr, zscore, percentile
                    "threshold": 0.95,
                    "orientation": "BOTH"
                }
            }
        }


class PathRequest(BaseModel):
    start_node_id: int
    end_node_id: int
    relationship_type: str = "RELATED"
    max_hops: int = 10


class LinkPredictionRequest(BaseModel):
    node_id: int
    relationship_type: str = "RELATED"
    options: Optional[dict] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "node_id": 123,
                "relationship_type": "KNOWS",
                "options": {
                    "topK": 10,
                    "similarityCutoff": 0.1,
                    "similarityMetric": "JACCARD"
                }
            }
        }


class NodePredictionRequest(BaseModel):
    node_label: str = "Node"
    property_name: str = Field(..., description="Property name to predict")
    relationship_type: Optional[str] = "RELATED"
    options: Optional[dict] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "node_label": "Person",
                "property_name": "age",
                "relationship_type": "KNOWS",
                "options": {
                    "knn_k": 10,
                    "embedding_dimension": 128
                }
            }
        }

class AnalysisResponse(BaseModel):
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Optional[dict] = None  # For additional information (e.g: execution time)


class DijkstraPathRequest(BaseModel):
    start_node_id: int
    end_node_id: int
    relationship_type: str = "RELATED"
    options: Optional[dict] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "start_node_id": 123,
                "end_node_id": 456,
                "relationship_type": "CONNECTED_TO",
                "options": {
                    "relationshipWeightProperty": "distance",
                    "graph_name": "my_graph"
                }
            }
        }


class AllShortestPathsRequest(BaseModel):
    start_node_id: int
    relationship_type: str = "RELATED"
    options: Optional[dict] = Field(default_factory=dict)


class NodeSearchRequest(BaseModel):
    label: Optional[str] = None
    property_filters: Optional[dict] = Field(default_factory=dict)
    limit: int = Field(default=100, le=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "label": "Person",
                "property_filters": {
                    "age": 30,
                    "city": "Paris"
                },
                "limit": 50
            }
        }


class NeighborsRequest(BaseModel):
    node_id: int
    relationship_type: Optional[str] = None
    direction: Literal["OUTGOING", "INCOMING", "UNDIRECTED"] = "UNDIRECTED"
    limit: int = Field(default=50, le=500)


class SubgraphRequest(BaseModel):
    node_ids: List[int] = Field(..., description="Node ids")


class ConnectionCheckRequest(BaseModel):
    start_node_id: int
    end_node_id: int
    relationship_type: Optional[str] = None
    max_hops: int = Field(default=5, le=10)