from fastapi import APIRouter, HTTPException
from app.models.schemas import CommunityRequest, AnalysisResponse
from app.services.community_service import CommunityService

router = APIRouter()
service = CommunityService()

@router.post("/louvain", response_model=AnalysisResponse)
async def detect_louvain_communities(request: CommunityRequest):
    """Detect community with Louvain"""
    try:
        result = service.detect_louvain(
            request.relationship_type,
            request.options
        )
        return AnalysisResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/greedy", response_model=AnalysisResponse)
async def detect_greedy_communities(request: CommunityRequest):
    """Detect community with Louvain"""
    try:
        result = service.detect_greedy(
            request.relationship_type,
            request.options
        )
        return AnalysisResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/wcc", response_model=AnalysisResponse)
async def detect_wcc(request: CommunityRequest):
    """Detect weakly connected components"""
    try:
        result = service.detect_weakly_connected_components(
            request.relationship_type,
            request.options
        )
        return AnalysisResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))