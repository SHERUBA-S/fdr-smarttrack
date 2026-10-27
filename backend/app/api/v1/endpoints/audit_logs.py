from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_roles
from app.models.audit import AuditLog
from app.models.enums import UserRole
from app.schemas.audit import AuditLogResponse, AuditLogListResponse

router = APIRouter()

@router.get("/", response_model=AuditLogListResponse)
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    search: Optional[str] = None,
    current_user = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.READONLY_AUDITOR])),
    db: Session = Depends(get_db)
):
    """View tamper-evident immutable audit trails (Super Admin and Auditor only)."""
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(AuditLog.details.ilike(s) | AuditLog.actor_email.ilike(s))

    total = query.count()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    offset = (page - 1) * page_size

    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size).all()

    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(l) for l in logs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
