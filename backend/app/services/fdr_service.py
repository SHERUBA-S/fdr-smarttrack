from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import func, desc, asc, or_
from sqlalchemy.orm import Session
from app.models.fdr import FDRRecord, FDRDocument, VerificationCheck
from app.models.institution import Institution, Bank
from app.models.workflow import RenewalRequest, ReleaseRequest
from app.models.enums import FDRStatus, VerificationOutcome, RequestStatus
from app.models.user import User
from app.models.enums import UserRole

def get_fdr_list(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    status_filter: Optional[FDRStatus] = None,
    institution_id: Optional[str] = None,
    bank_name: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    has_discrepancy: Optional[bool] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Tuple[List[FDRRecord], int]:
    """Retrieve filtered, paginated FDR records with multi-tenant data isolation."""
    query = db.query(FDRRecord)

    # Multi-tenant isolation: Institution users can ONLY see their own institution's FDRs
    if user.role == UserRole.INSTITUTION_USER:
        if not user.institution_id:
            return [], 0
        query = query.filter(FDRRecord.institution_id == user.institution_id)
    elif institution_id:
        query = query.filter(FDRRecord.institution_id == institution_id)

    # Filters
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(or_(
            FDRRecord.fdr_number.ilike(s),
            FDRRecord.bank_name.ilike(s),
            FDRRecord.purpose.ilike(s)
        ))

    if status_filter:
        query = query.filter(FDRRecord.status == status_filter)

    if bank_name:
        query = query.filter(FDRRecord.bank_name.ilike(f"%{bank_name}%"))

    if from_date:
        query = query.filter(FDRRecord.maturity_date >= from_date)

    if to_date:
        query = query.filter(FDRRecord.maturity_date <= to_date)

    if has_discrepancy is not None:
        query = query.filter(FDRRecord.has_discrepancy == has_discrepancy)

    total = query.count()

    # Sorting
    sort_column = getattr(FDRRecord, sort_by, FDRRecord.created_at)
    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    # Pagination
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return items, total

def get_dashboard_metrics(db: Session, user: User) -> Dict[str, Any]:
    """Aggregate real database statistics for administrative and institution dashboards."""
    base_fdr = db.query(FDRRecord)
    if user.role == UserRole.INSTITUTION_USER:
        base_fdr = base_fdr.filter(FDRRecord.institution_id == user.institution_id)

    today = date.today()
    in_30_days = today + timedelta(days=30)

    # Metric counts
    total_fdrs = base_fdr.count()
    
    # Total Principal Amount
    total_principal_res = base_fdr.with_entities(func.sum(FDRRecord.principal_amount)).scalar()
    total_recorded_principal = total_principal_res or Decimal("0.00")

    records_awaiting_review = base_fdr.filter(
        FDRRecord.status.in_([FDRStatus.SUBMITTED, FDRStatus.UNDER_REVIEW])
    ).count()

    records_with_discrepancies = base_fdr.filter(FDRRecord.has_discrepancy == True).count()

    fdrs_approaching_30d = base_fdr.filter(
        FDRRecord.maturity_date >= today,
        FDRRecord.maturity_date <= in_30_days,
        FDRRecord.status.notin_([FDRStatus.RELEASED, FDRStatus.EXPIRED])
    ).count()

    fdrs_overdue = base_fdr.filter(
        FDRRecord.maturity_date < today,
        FDRRecord.status.notin_([FDRStatus.RELEASED, FDRStatus.EXPIRED])
    ).count()

    # Renewal & release requests pending
    renewal_q = db.query(RenewalRequest).filter(RenewalRequest.status == RequestStatus.PENDING)
    release_q = db.query(ReleaseRequest).filter(ReleaseRequest.status == RequestStatus.PENDING)
    if user.role == UserRole.INSTITUTION_USER:
        renewal_q = renewal_q.join(FDRRecord).filter(FDRRecord.institution_id == user.institution_id)
        release_q = release_q.join(FDRRecord).filter(FDRRecord.institution_id == user.institution_id)

    pending_renewals = renewal_q.count()
    pending_releases = release_q.count()

    # Documents requiring verification
    docs_to_verify = base_fdr.filter(
        FDRRecord.verification_status.in_([
            VerificationOutcome.AWAITING_EXTERNAL,
            VerificationOutcome.WARNING,
            VerificationOutcome.NOT_CHECKED
        ])
    ).count()

    # Status distribution
    status_group = base_fdr.with_entities(
        FDRRecord.status, func.count(FDRRecord.id)
    ).group_by(FDRRecord.status).all()
    status_distribution = [{"status": s.value, "count": cnt} for s, cnt in status_group]

    # Bank distribution (Top 6)
    bank_group = base_fdr.with_entities(
        FDRRecord.bank_name,
        func.count(FDRRecord.id),
        func.sum(FDRRecord.principal_amount)
    ).group_by(FDRRecord.bank_name).order_by(desc(func.count(FDRRecord.id))).limit(6).all()
    bank_distribution = [
        {"bank_name": b, "count": c, "total_amount": amt or Decimal("0.00")}
        for b, c, amt in bank_group
    ]

    # Maturity timeline (next 12 months)
    timeline_items = []
    for m in range(12):
        # Rough 30-day buckets for monthly projections
        start_m = today + timedelta(days=m * 30)
        end_m = today + timedelta(days=(m + 1) * 30)
        label = start_m.strftime("%b %Y")
        
        m_stats = base_fdr.filter(
            FDRRecord.maturity_date >= start_m,
            FDRRecord.maturity_date < end_m
        ).with_entities(
            func.count(FDRRecord.id),
            func.sum(FDRRecord.principal_amount)
        ).first()

        cnt = m_stats[0] if m_stats and m_stats[0] else 0
        amt = m_stats[1] if m_stats and m_stats[1] else Decimal("0.00")
        timeline_items.append({"month_year": label, "count": cnt, "total_amount": amt})

    # Urgent Actions (overdue or <= 30 days or pending reviews)
    urgent_records = base_fdr.filter(
        or_(
            FDRRecord.maturity_date <= in_30_days,
            FDRRecord.has_discrepancy == True,
            FDRRecord.status.in_([FDRStatus.RENEWAL_PENDING, FDRStatus.RELEASE_REQUESTED])
        )
    ).order_by(asc(FDRRecord.maturity_date)).limit(10).all()

    urgent_actions = []
    for rec in urgent_records:
        days = (rec.maturity_date - today).days
        if days < 0:
            urgency = "OVERDUE"
            act_type = "RENEWAL_DUE"
        elif days <= 7:
            urgency = "CRITICAL"
            act_type = "RENEWAL_DUE"
        elif rec.has_discrepancy:
            urgency = "HIGH"
            act_type = "DISCREPANCY_FLAG"
        elif rec.status == FDRStatus.RENEWAL_PENDING:
            urgency = "HIGH"
            act_type = "RENEWAL_REVIEW"
        elif rec.status == FDRStatus.RELEASE_REQUESTED:
            urgency = "HIGH"
            act_type = "RELEASE_REVIEW"
        else:
            urgency = "WARNING"
            act_type = "UPCOMING_MATURITY"

        urgent_actions.append({
            "fdr_id": rec.id,
            "fdr_number": rec.fdr_number,
            "institution_name": rec.institution.name if rec.institution else "Unknown",
            "bank_name": rec.bank_name,
            "principal_amount": rec.principal_amount,
            "maturity_date": rec.maturity_date,
            "days_to_maturity": days,
            "status": rec.status.value,
            "urgency": urgency,
            "action_type": act_type
        })

    # Total Institutions
    total_institutions = db.query(Institution).count() if user.role != UserRole.INSTITUTION_USER else 1

    return {
        "total_institutions": total_institutions,
        "total_fdrs": total_fdrs,
        "total_recorded_principal": total_recorded_principal,
        "records_awaiting_review": records_awaiting_review,
        "records_with_discrepancies": records_with_discrepancies,
        "fdrs_approaching_maturity_30d": fdrs_approaching_30d,
        "fdrs_overdue_maturity": fdrs_overdue,
        "pending_renewal_requests": pending_renewals,
        "pending_release_requests": pending_releases,
        "documents_requiring_verification": docs_to_verify,
        "status_distribution": status_distribution,
        "maturity_timeline": timeline_items,
        "bank_distribution": bank_distribution,
        "urgent_actions": urgent_actions
    }
