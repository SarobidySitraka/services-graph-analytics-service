from fastapi import APIRouter, HTTPException
from app.models.schemas import CentralityRequest, AnalysisResponse
from app.services.centrality_service import CentralityService

router = APIRouter()
service = CentralityService()

@router.post("/betweenness", response_model=AnalysisResponse)
async def get_betweenness_centrality(request: CentralityRequest):
    """Calculate the betweenness centrality"""
    try:
        result = service.calculate_betweenness(
            request.relationship_type,
            request.options
        )
        return AnalysisResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/closeness", response_model=AnalysisResponse)
async def get_closeness_centrality(request: CentralityRequest):
    """Calculate the closeness centrality"""
    try:
        result = service.calculate_closeness(
            request.relationship_type,
            request.options
        )
        return AnalysisResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/degree", response_model=AnalysisResponse)
async def get_degree_centrality(request: CentralityRequest):
    """Calculate the degree centrality"""
    try:
        result = service.calculate_degree(
            request.relationship_type,
            request.options
        )
        return AnalysisResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pagerank", response_model=AnalysisResponse)
async def get_pagerank(request: CentralityRequest):
    """Calculate the PageRank"""
    try:
        result = service.calculate_pagerank(
            request.relationship_type,
            request.options
        )
        return AnalysisResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))