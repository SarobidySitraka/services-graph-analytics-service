from fastapi import APIRouter, HTTPException
from app.models.schemas import AnomalyRequest, AnalysisResponse
from app.services.anomaly_service import AnomalyService

router = APIRouter()
service = AnomalyService()


@router.post("/detect", response_model=AnalysisResponse)
async def detect_anomalies(request: AnomalyRequest):
    """
    Detect anomalous nodes based on their degree

    Available methods:
    - percentile: Nodes above a percentile (default: 95%)
    - zscore: Nodes with Z-score > threshold (default: 3)
    - iqr: Nodes outside the Interquartile Range (IQR * 1.5 )
    """
    try:
        result = service.detect_outliers(
            request.node_label,
            request.relationship_type,
            request.options
        )
        return AnalysisResponse(
            success=True,
            data=result,
            metadata={
                "method": request.options.get("method", "percentile"),
                "node_label": request.node_label
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))