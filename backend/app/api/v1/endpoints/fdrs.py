import io
import csv
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles, verify_institution_access
from app.models.fdr import FDRRecord, FDRDocument, VerificationCheck
from app.models.institution import Institution
from app.models.user import User
from app.models.enums import UserRole, FDRStatus, VerificationOutcome
from app.schemas.fdr import FDRCreate, FDRUpdate, FDRResponse, FDRListResponse
from app.services.fdr_service import get_fdr_list
from app.services.verification_engine import VerificationEngine
from app.services.anomaly_detector import AnomalyDetector
from app.services.audit_service import log_audit_event
from app.services.lifecycle_service import (
    RiskRadarEngine, ConsistencyCheckerEngine, LifecycleChainEngine,
    MaturityCalendarEngine, sanitize_csv_cell
)

router = APIRouter()

@router.get("/", response_model=FDRListResponse)
def list_fdrs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[FDRStatus] = None,
    institution_id: Optional[str] = None,
    bank_name: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    has_discrepancy: Optional[bool] = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List FDR records with multi-criteria filtering, search, sorting and role-based data isolation."""
    items, total = get_fdr_list(
        db=db,
        user=current_user,
        page=page,
        page_size=page_size,
        search=search,
        status_filter=status,
        institution_id=institution_id,
        bank_name=bank_name,
        from_date=from_date,
        to_date=to_date,
        has_discrepancy=has_discrepancy,
        sort_by=sort_by,
        sort_order=sort_order
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return FDRListResponse(
        items=[FDRResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/risk-radar")
def get_risk_radar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Explainable rule-based Risk Radar with deterministic priorities and human-readable reasoning."""
    return RiskRadarEngine.get_radar_summary(db=db, user=current_user)

@router.get("/consistency-checker")
def get_consistency_checks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Document & data consistency audit identifying date mismatches, missing fields, and unverified records."""
    return ConsistencyCheckerEngine.run_checks(db=db, user=current_user)

@router.get("/maturity-calendar")
def get_maturity_calendar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Maturity countdown timeline categorizing FDRs into 7, 15, 30 day reminder windows and overdue buckets."""
    return MaturityCalendarEngine.get_calendar_buckets(db=db, user=current_user)

@router.get("/lifecycle-chains")
def get_lifecycle_chains(
    limit: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Traceable audit chains showing creation, uploads, checks, renewals, and release events."""
    return LifecycleChainEngine.get_all_chains_summary(db=db, user=current_user, limit=limit)

@router.get("/export-csv")
def export_fdrs_csv(
    status: Optional[FDRStatus] = None,
    bank_name: Optional[str] = None,
    has_discrepancy: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export FDR register records as a secure CSV (sanitized against formula injection)."""
    items, total = get_fdr_list(
        db=db,
        user=current_user,
        page=1,
        page_size=5000,
        status_filter=status,
        bank_name=bank_name,
        has_discrepancy=has_discrepancy
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "FDR ID", "FDR Reference Number", "Bank Name", "Branch",
        "Principal Amount (INR)", "Interest Rate (%)", "Issue Date", "Maturity Date",
        "Status", "Verification Status", "Discrepancy Flag", "Discrepancy Notes",
        "Created Date"
    ])

    for f in items:
        writer.writerow([
            sanitize_csv_cell(f.id),
            sanitize_csv_cell(f.fdr_number),
            sanitize_csv_cell(f.bank_name),
            sanitize_csv_cell(f.branch_name or "N/A"),
            sanitize_csv_cell(f.principal_amount),
            sanitize_csv_cell(f.interest_rate or "N/A"),
            sanitize_csv_cell(f.issue_date),
            sanitize_csv_cell(f.maturity_date),
            sanitize_csv_cell(f.status.value),
            sanitize_csv_cell(f.verification_status.value),
            sanitize_csv_cell("YES" if f.has_discrepancy else "NO"),
            sanitize_csv_cell(f.discrepancy_notes or ""),
            sanitize_csv_cell(f.created_at.strftime("%Y-%m-%d %H:%M:%S") if f.created_at else "")
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=fdr_guardian_register.csv"}
    )

@router.get("/{fdr_id}/lifecycle-chain")
def get_single_fdr_chain(
    fdr_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve the full chronological chain of custody and events for a single FDR."""
    fdr = db.query(FDRRecord).filter(FDRRecord.id == fdr_id).first()
    if not fdr:
        raise HTTPException(status_code=404, detail="FDR record not found")
    verify_institution_access(current_user, fdr.institution_id)
    return LifecycleChainEngine.get_fdr_chain(db=db, fdr_id=fdr_id)

@router.get("/{fdr_id}", response_model=FDRResponse)
def get_fdr_detail(
    fdr_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve full FDR record with attached documents, OCR fields, and verification checks."""
    fdr = db.query(FDRRecord).filter(FDRRecord.id == fdr_id).first()
    if not fdr:
        raise HTTPException(status_code=404, detail="FDR record not found")

    verify_institution_access(current_user, fdr.institution_id)
    return FDRResponse.model_validate(fdr)

@router.post("/", response_model=FDRResponse, status_code=status.HTTP_201_CREATED)
def create_fdr(
    data: FDRCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new FDR record, run deterministic verification and ML anomaly detection."""
    verify_institution_access(current_user, data.institution_id)

    # Validate institution exists
    inst = db.query(Institution).filter(Institution.id == data.institution_id).first()
    if not inst:
        raise HTTPException(status_code=400, detail="Invalid institution ID")

    fdr = FDRRecord(
        fdr_number=data.fdr_number.strip().upper(),
        institution_id=data.institution_id,
        bank_id=data.bank_id,
        bank_name=data.bank_name.strip(),
        branch_name=data.branch_name,
        principal_amount=data.principal_amount,
        currency=data.currency,
        interest_rate=data.interest_rate,
        issue_date=data.issue_date,
        maturity_date=data.maturity_date,
        purpose=data.purpose,
        status=FDRStatus.SUBMITTED,
        verification_status=VerificationOutcome.NOT_CHECKED,
        is_synthetic=False
    )
    db.add(fdr)
    db.commit()
    db.refresh(fdr)

    # Execute verification checks
    VerificationEngine.run_all_checks(db, fdr)

    # Calculate experimental ML anomaly score
    score, signal = AnomalyDetector.evaluate_fdr(fdr)
    fdr.anomaly_score = score
    db.commit()
    db.refresh(fdr)

    log_audit_event(
        db=db,
        action="FDR_CREATED",
        entity_type="FDR",
        entity_id=fdr.id,
        actor=current_user,
        details=f"Created FDR #{fdr.fdr_number} for {fdr.bank_name}. Principal: ₹{fdr.principal_amount:,.2f}"
    )

    return FDRResponse.model_validate(fdr)

@router.put("/{fdr_id}", response_model=FDRResponse)
def update_fdr(
    fdr_id: str,
    data: FDRUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update FDR record fields and re-run verification."""
    fdr = db.query(FDRRecord).filter(FDRRecord.id == fdr_id).first()
    if not fdr:
        raise HTTPException(status_code=404, detail="FDR record not found")

    verify_institution_access(current_user, fdr.institution_id)

    # Only Reviewers / Admins can update status directly
    if data.status and current_user.role not in [UserRole.SUPER_ADMIN, UserRole.REVIEWING_OFFICIAL]:
        raise HTTPException(status_code=403, detail="Only reviewing officials or admins can update status directly")

    update_dict = data.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(fdr, field, val)

    db.commit()

    # Re-run verification suite
    VerificationEngine.run_all_checks(db, fdr)
    score, _ = AnomalyDetector.evaluate_fdr(fdr)
    fdr.anomaly_score = score
    db.commit()
    db.refresh(fdr)

    log_audit_event(
        db=db,
        action="FDR_UPDATED",
        entity_type="FDR",
        entity_id=fdr.id,
        actor=current_user,
        details=f"Updated fields: {list(update_dict.keys())}"
    )

    return FDRResponse.model_validate(fdr)

@router.post("/{fdr_id}/verify", response_model=FDRResponse)
def trigger_verification(
    fdr_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger complete verification check suite and ML anomaly assessment."""
    fdr = db.query(FDRRecord).filter(FDRRecord.id == fdr_id).first()
    if not fdr:
        raise HTTPException(status_code=404, detail="FDR record not found")

    verify_institution_access(current_user, fdr.institution_id)

    VerificationEngine.run_all_checks(db, fdr)
    score, signal = AnomalyDetector.evaluate_fdr(fdr)
    fdr.anomaly_score = score
    db.commit()
    db.refresh(fdr)

    log_audit_event(
        db=db,
        action="FDR_VERIFICATION_TRIGGERED",
        entity_type="FDR",
        entity_id=fdr.id,
        actor=current_user,
        details=f"Verification status: {fdr.verification_status.value}. Anomaly score: {score}"
    )

    return FDRResponse.model_validate(fdr)
