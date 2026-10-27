from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.dashboard import DashboardMetricsResponse
from app.services.fdr_service import get_dashboard_metrics

router = APIRouter()

@router.get("/metrics", response_model=DashboardMetricsResponse)
def get_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get live aggregated analytics, charts, and priority action items
    calculated from PostgreSQL queries respecting institution isolation.
    """
    data = get_dashboard_metrics(db, current_user)
    return DashboardMetricsResponse(**data)
