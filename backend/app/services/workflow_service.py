from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.fdr import FDRRecord
from app.models.workflow import RenewalRequest, ReleaseRequest, ReviewDecision
from app.models.enums import FDRStatus, RequestStatus, UserRole
from app.models.user import User
from app.services.audit_service import log_audit_event
from app.services.notification_service import create_notification

def submit_renewal_request(
    db: Session,
    fdr_id: str,
    new_maturity_date,
    rationale: str,
    user: User,
    supporting_doc_name: Optional[str] = None
) -> RenewalRequest:
    """Submit an FDR renewal request."""
    fdr = db.query(FDRRecord).filter(FDRRecord.id == fdr_id).first()
    if not fdr:
        raise HTTPException(status_code=404, detail="FDR record not found")
        
    if new_maturity_date <= fdr.maturity_date:
        raise HTTPException(status_code=400, detail="New maturity date must be after current maturity date")
        
    # Check if there is already a pending renewal
    existing = db.query(RenewalRequest).filter(
        RenewalRequest.fdr_id == fdr_id,
        RenewalRequest.status == RequestStatus.PENDING
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="A renewal request is already pending for this FDR")

    renewal = RenewalRequest(
        fdr_id=fdr_id,
        requested_by_id=user.id,
        new_maturity_date=new_maturity_date,
        rationale=rationale,
        supporting_doc_name=supporting_doc_name,
        status=RequestStatus.PENDING
    )
    db.add(renewal)
    
    # Update FDR status
    prev_status = fdr.status
    fdr.status = FDRStatus.RENEWAL_PENDING
    db.commit()
    db.refresh(renewal)

    log_audit_event(
        db=db,
        action="FDR_RENEWAL_REQUEST_SUBMITTED",
        entity_type="FDR",
        entity_id=fdr.id,
        actor=user,
        details=f"Renewal requested to {new_maturity_date}. Rationale: {rationale}",
        before_state={"status": prev_status.value},
        after_state={"status": fdr.status.value, "renewal_id": renewal.id}
    )

    return renewal

def submit_release_request(
    db: Session,
    fdr_id: str,
    clearance_reference: str,
    rationale: str,
    user: User,
    supporting_doc_name: Optional[str] = None
) -> ReleaseRequest:
    """Submit an FDR release request."""
    fdr = db.query(FDRRecord).filter(FDRRecord.id == fdr_id).first()
    if not fdr:
        raise HTTPException(status_code=404, detail="FDR record not found")

    existing = db.query(ReleaseRequest).filter(
        ReleaseRequest.fdr_id == fdr_id,
        ReleaseRequest.status == RequestStatus.PENDING
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="A release request is already pending for this FDR")

    release = ReleaseRequest(
        fdr_id=fdr_id,
        requested_by_id=user.id,
        clearance_reference=clearance_reference,
        rationale=rationale,
        supporting_doc_name=supporting_doc_name,
        status=RequestStatus.PENDING
    )
    db.add(release)
    
    prev_status = fdr.status
    fdr.status = FDRStatus.RELEASE_REQUESTED
    db.commit()
    db.refresh(release)

    log_audit_event(
        db=db,
        action="FDR_RELEASE_REQUEST_SUBMITTED",
        entity_type="FDR",
        entity_id=fdr.id,
        actor=user,
        details=f"Release requested with clearance ref: {clearance_reference}. Rationale: {rationale}",
        before_state={"status": prev_status.value},
        after_state={"status": fdr.status.value, "release_id": release.id}
    )

    return release

def process_review_decision(
    db: Session,
    fdr_id: str,
    reviewer: User,
    decision_type: str,
    new_status: FDRStatus,
    reason: str,
    remarks: Optional[str] = None
) -> ReviewDecision:
    """Process official review decision on an FDR or pending workflow request."""
    fdr = db.query(FDRRecord).filter(FDRRecord.id == fdr_id).first()
    if not fdr:
        raise HTTPException(status_code=404, detail="FDR record not found")

    prev_status = fdr.status
    
    # Handle pending requests if applicable
    if decision_type == "RENEW":
        pending_renewal = db.query(RenewalRequest).filter(
            RenewalRequest.fdr_id == fdr_id,
            RenewalRequest.status == RequestStatus.PENDING
        ).first()
        if pending_renewal:
            pending_renewal.status = RequestStatus.APPROVED
            pending_renewal.resolved_at = datetime.now(timezone.utc)
            fdr.maturity_date = pending_renewal.new_maturity_date
            new_status = FDRStatus.APPROVED
            
    elif decision_type == "RELEASE":
        pending_release = db.query(ReleaseRequest).filter(
            ReleaseRequest.fdr_id == fdr_id,
            ReleaseRequest.status == RequestStatus.PENDING
        ).first()
        if pending_release:
            pending_release.status = RequestStatus.APPROVED
            pending_release.resolved_at = datetime.now(timezone.utc)
            new_status = FDRStatus.RELEASED

    decision = ReviewDecision(
        fdr_id=fdr.id,
        reviewer_id=reviewer.id,
        previous_status=prev_status,
        new_status=new_status,
        decision_type=decision_type,
        reason=reason,
        remarks=remarks
    )
    db.add(decision)
    fdr.status = new_status
    fdr.assigned_reviewer_id = reviewer.id
    db.commit()
    db.refresh(decision)

    # Audit log
    log_audit_event(
        db=db,
        action=f"REVIEW_DECISION_{decision_type}",
        entity_type="FDR",
        entity_id=fdr.id,
        actor=reviewer,
        details=f"Decision: {decision_type} -> {new_status.value}. Reason: {reason}",
        before_state={"status": prev_status.value},
        after_state={"status": new_status.value, "decision_id": decision.id}
    )

    # Notify institution members
    inst_users = db.query(User).filter(
        User.institution_id == fdr.institution_id,
        User.role == UserRole.INSTITUTION_USER
    ).all()
    for u in inst_users:
        create_notification(
            db=db,
            user_id=u.id,
            title=f"FDR #{fdr.fdr_number} Status Update: {new_status.value}",
            message=f"Official decision on FDR #{fdr.fdr_number}: {decision_type} ({reason})",
            category="REVIEW_UPDATE",
            link=f"/fdrs/{fdr.id}",
            fdr_id=fdr.id
        )

    return decision
