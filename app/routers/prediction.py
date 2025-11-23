from fastapi import APIRouter, HTTPException
from app.models.schemas import LinkPredictionRequest, NodePredictionRequest, AnalysisResponse
from app.services.prediction_service import PredictionService

router = APIRouter()
service = PredictionService()


@router.post("/links", response_model=AnalysisResponse)
async def predict_links(request: LinkPredictionRequest):
    """
    Predict future links using Node Similarity (GDS)

    Available options:
    - topK: Number of suggestions (default: 10)
    - similarityCutoff: Minimum similarity threshold (default: 0.0)
    - similarityMetric: JACCARD, COSINE, OVERLAP (default: JACCARD)
    """
    try:
        result = service.predict_links(
            request.node_id,
            request.relationship_type,
            request.options
        )
        return AnalysisResponse(
            success=True,
            data=result,
            metadata={
                "node_id": request.node_id,
                "metric": request.options.get("similarityMetric", "JACCARD")
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/node-properties", response_model=AnalysisResponse)
async def predict_node_properties(request: NodePredictionRequest):
    """
    Predict missing node properties

    UUses KNN based on shared relationships

    Available options:
    - knn_k: Number of neighbors for prediction (default: 10)
    - embedding_dimension: Dimension of embeddings if using GDS (default: 128)
    """
    try:
        result = service.predict_node_properties(
            request.node_label,
            request.property_name,
            request.options
        )
        return AnalysisResponse(
            success=True,
            data=result,
            metadata={
                "node_label": request.node_label,
                "property": request.property_name,
                "knn_k": request.options.get("knn_k", 10),
                "method": "simple_knn"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/node-properties-advanced", response_model=AnalysisResponse)
async def predict_node_properties_advanced(request: NodePredictionRequest):
    """
    Predict missing properties using GDS FastRP + KNN (advanced method)

    Pipeline:
    1. Create a GDS projected graph
    2. Compute FastRP embeddings for each node
    3. Use KNN on the embeddings to find similar nodes
    4. Predict missing values via weighted average
    5. Automatically clean up temporary resources

    Available options:
    - knn_k: Number of neighbors (default: 10)
    - embedding_dimension: Embedding dimension (default: 128)
    - graph_name: Name of the temporary graph (auto-generated if not provided)

    Slower but more accurate than the simple method
    """
    try:
        if not request.relationship_type:
            raise HTTPException(
                status_code=400,
                detail="relationship_type is required for advanced prediction"
            )

        result = service.predict_node_properties_with_gds(
            request.node_label,
            request.property_name,
            request.relationship_type,
            request.options
        )
        return AnalysisResponse(
            success=True,
            data=result,
            metadata={
                "node_label": request.node_label,
                "property": request.property_name,
                "knn_k": request.options.get("knn_k", 10),
                "embedding_dimension": request.options.get("embedding_dimension", 128),
                "method": "gds_fastrp_knn"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))