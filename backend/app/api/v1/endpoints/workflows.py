from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles, verify_institution_access
from app.models.fdr import FDRRecord
from app.models.workflow import RenewalRequest, ReleaseRequest, ReviewDecision
from app.models.enums import UserRole, FDRStatus, RequestStatus
from app.models.user import User
from app.schemas.workflow import (
    RenewalRequestCreate, RenewalResponse,
    ReleaseRequestCreate, ReleaseResponse,
    ReviewDecisionCreate, ReviewDecisionResponse
)
from app.services.workflow_service import (
    submit_renewal_request, submit_release_request, process_review_decision
)

router = APIRouter()

@router.post("/fdrs/{fdr_id}/renew", response_model=RenewalResponse)
def request_renewal(
    fdr_id: str,
    data: RenewalRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit an FDR renewal request with rationale and new maturity date."""
    fdr = db.query(FDRRecord).filter(FDRRecord.id == fdr_id).first()
    if not fdr:
        raise HTTPException(status_code=404, detail="FDR record not found")

    verify_institution_access(current_user, fdr.institution_id)

    res = submit_renewal_request(
        db=db,
        fdr_id=fdr_id,
        new_maturity_date=data.new_maturity_date,
        rationale=data.rationale,
        user=current_user,
        supporting_doc_name=data.supporting_doc_name
    )
    return RenewalResponse.model_validate(res)

@router.post("/fdrs/{fdr_id}/release", response_model=ReleaseResponse)
def request_release(
    fdr_id: str,
    data: ReleaseRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit an FDR release request with clearance reference."""
    fdr = db.query(FDRRecord).filter(FDRRecord.id == fdr_id).first()
    if not fdr:
        raise HTTPException(status_code=404, detail="FDR record not found")

    verify_institution_access(current_user, fdr.institution_id)

    res = submit_release_request(
        db=db,
        fdr_id=fdr_id,
        clearance_reference=data.clearance_reference,
        rationale=data.rationale,
        user=current_user,
        supporting_doc_name=data.supporting_doc_name
    )
    return ReleaseResponse.model_validate(res)

@router.post("/fdrs/{fdr_id}/decide", response_model=ReviewDecisionResponse)
def make_review_decision(
    fdr_id: str,
    data: ReviewDecisionCreate,
    current_user: User = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.REVIEWING_OFFICIAL])),
    db: Session = Depends(get_db)
):
    """Record official review decision (Approve, Reject, Request Info, Renew, Release)."""
    decision = process_review_decision(
        db=db,
        fdr_id=fdr_id,
        reviewer=current_user,
        decision_type=data.decision_type,
        new_status=data.new_status,
        reason=data.reason,
        remarks=data.remarks
    )
    return ReviewDecisionResponse.model_validate(decision)

@router.get("/review-queue")
def get_review_queue(
    current_user: User = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.REVIEWING_OFFICIAL])),
    db: Session = Depends(get_db)
):
    """Retrieve prioritized review queue of submitted, renewal pending, and release requested FDRs."""
    pending_fdrs = db.query(FDRRecord).filter(
        FDRRecord.status.in_([
            FDRStatus.SUBMITTED,
            FDRStatus.UNDER_REVIEW,
            FDRStatus.RENEWAL_PENDING,
            FDRStatus.RELEASE_REQUESTED,
            FDRStatus.ADDITIONAL_INFO_REQUIRED
        ])
    ).order_by(FDRRecord.has_discrepancy.desc(), FDRRecord.created_at.asc()).all()

    items = []
    for f in pending_fdrs:
        items.append({
            "id": f.id,
            "fdr_number": f.fdr_number,
            "institution_name": f.institution.name if f.institution else "Unknown",
            "bank_name": f.bank_name,
            "principal_amount": f.principal_amount,
            "maturity_date": f.maturity_date,
            "status": f.status.value,
            "has_discrepancy": f.has_discrepancy,
            "discrepancy_notes": f.discrepancy_notes,
            "anomaly_score": f.anomaly_score,
            "created_at": f.created_at
        })

    return {"total": len(items), "items": items}

@router.get("/bottlenecks")
def get_bottlenecks(
    current_user: User = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.REVIEWING_OFFICIAL])),
    db: Session = Depends(get_db)
):
    """Retrieve queue bottlenecks, queue ages, and SLA threshold violations."""
    from app.services.lifecycle_service import BottleneckMonitorEngine
    return BottleneckMonitorEngine.get_bottlenecks(db)

