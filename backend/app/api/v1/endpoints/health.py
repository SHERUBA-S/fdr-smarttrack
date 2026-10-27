from fastapi import APIRouter, status, Response
from app.core.database import check_db_health
from app.services.ocr_service import OCRService
from app.services.anomaly_detector import AnomalyDetector

router = APIRouter()

@router.get("/health")
def health_check(response: Response):
    """
    Service health check:
    - PostgreSQL database connectivity
    - OCR engine status
    - ML anomaly model status
    """
    db_ok = check_db_health()
    ocr_ok = OCRService.is_ocr_engine_available()
    
    # Try anomaly detector initialization
    try:
        AnomalyDetector.load_or_train_baseline()
        ml_ok = True
    except Exception:
        ml_ok = False

    status_code = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    response.status_code = status_code

    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": {
            "status": "connected" if db_ok else "disconnected",
            "type": "PostgreSQL",
            "required": True
        },
        "ocr_engine": {
            "available": ocr_ok,
            "engine": "Tesseract OCR / PDF Text Parser",
            "note": "Fully functional PDF text extraction always available; Tesseract image OCR active if installed."
        },
        "anomaly_detector": {
            "available": ml_ok,
            "engine": "scikit-learn IsolationForest",
            "schema_features": AnomalyDetector.get_feature_schema()
        }
    }
