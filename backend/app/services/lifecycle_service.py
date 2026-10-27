"""
Lifecycle Service: Explainable Risk Radar, Consistency Checker,
Traceable Lifecycle Chain, Maturity Calendar, and Bottleneck Monitor.
"""
from datetime import date, datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set
from collections import defaultdict
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.models.fdr import FDRRecord, FDRDocument, VerificationCheck
from app.models.workflow import RenewalRequest, ReleaseRequest, ReviewDecision
from app.models.institution import Institution
from app.models.user import User
from app.models.enums import UserRole, FDRStatus, VerificationOutcome, RequestStatus

def sanitize_csv_cell(val: Any) -> str:
    """Prevent CSV formula injection by prepending quote if cell starts with dangerous chars."""
    if val is None:
        return ""
    s = str(val).strip()
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{s}"
    return s

def calculate_days_remaining(maturity_date: date) -> int:
    today = date.today()
    return (maturity_date - today).days

class RiskRadarEngine:
    """
    Deterministic, explainable, rule-based FDR Risk Radar.
    Evaluates maturity proximity, document absence, verification delays, and workflow staleness.
    """
    @staticmethod
    def analyze_fdr(
        fdr: FDRRecord,
        db: Optional[Session] = None,
        doc_fdr_ids: Optional[Set[str]] = None,
        renewals_by_fdr: Optional[Dict[str, List[RenewalRequest]]] = None
    ) -> Dict[str, Any]:
        days_left = calculate_days_remaining(fdr.maturity_date)
        triggered_rules = []
        risk_points = 0

        # Rule 1: Maturity Status
        if days_left < 0:
            risk_points += 40
            triggered_rules.append({
                "rule_id": "RULE_MATURITY_OVERDUE",
                "severity": "CRITICAL",
                "title": "Maturity Date Passed (Overdue)",
                "explanation": f"This FDR matured on {fdr.maturity_date} ({abs(days_left)} days ago) and requires immediate renewal or statutory release.",
                "action": "Initiate renewal request or seek clearance release"
            })
        elif days_left <= 7:
            risk_points += 30
            triggered_rules.append({
                "rule_id": "RULE_MATURITY_7_DAYS",
                "severity": "HIGH",
                "title": "Maturing Within 7 Days",
                "explanation": f"Deposit expires in {days_left} day(s) on {fdr.maturity_date}. High priority for compliance continuity.",
                "action": "Urgent renewal follow-up with issuing bank"
            })
        elif days_left <= 30:
            risk_points += 15
            triggered_rules.append({
                "rule_id": "RULE_MATURITY_30_DAYS",
                "severity": "MEDIUM",
                "title": "Maturing Within 30 Days",
                "explanation": f"Deposit expires in {days_left} days on {fdr.maturity_date}. Advance notice window active.",
                "action": "Prepare renewal documentation with institution"
            })

        # Rule 2: Document Completeness (Batch-aware)
        if doc_fdr_ids is not None:
            has_doc = fdr.id in doc_fdr_ids
            doc_count = 1 if has_doc else 0
        elif db:
            doc_count = db.query(FDRDocument).filter(FDRDocument.fdr_id == fdr.id).count()
        else:
            doc_count = 0

        if doc_count == 0:
            risk_points += 25
            triggered_rules.append({
                "rule_id": "RULE_MISSING_DOCUMENT",
                "severity": "HIGH",
                "title": "Missing Physical/Scanned Receipt",
                "explanation": "No scanned fixed deposit receipt or deposit advice PDF has been uploaded for verification.",
                "action": "Upload official bank FDR receipt document"
            })

        # Rule 3: Verification Outcome & Discrepancies
        if fdr.has_discrepancy:
            risk_points += 35
            triggered_rules.append({
                "rule_id": "RULE_DISCREPANCY_FLAGGED",
                "severity": "CRITICAL",
                "title": "Active Data Discrepancy",
                "explanation": fdr.discrepancy_notes or "Field mismatch or anomaly identified during verification checks.",
                "action": "Conduct manual officer review and request clarifying documents"
            })
        elif fdr.verification_status == VerificationOutcome.FAILED:
            risk_points += 30
            triggered_rules.append({
                "rule_id": "RULE_VERIFICATION_FAILED",
                "severity": "HIGH",
                "title": "Verification Checks Failed",
                "explanation": "Automated deterministic verification checks identified one or more failed validation criteria.",
                "action": "Review failure evidence on FDR detail page"
            })
        elif fdr.verification_status == VerificationOutcome.WARNING:
            risk_points += 15
            triggered_rules.append({
                "rule_id": "RULE_VERIFICATION_WARNING",
                "severity": "MEDIUM",
                "title": "Verification Warning",
                "explanation": "Verification checks generated warning alerts requiring human supervisory review.",
                "action": "Review warning items and confirm or correct fields"
            })

        # Rule 4: Stale Workflows (Batch-aware)
        if renewals_by_fdr is not None:
            pending_renewals = renewals_by_fdr.get(fdr.id, [])
        elif db:
            pending_renewals = db.query(RenewalRequest).filter(
                RenewalRequest.fdr_id == fdr.id,
                RenewalRequest.status == RequestStatus.PENDING
            ).all()
        else:
            pending_renewals = []

        now_utc = datetime.now(timezone.utc)
        for ren in pending_renewals:
            created_tz = ren.created_at if ren.created_at.tzinfo else ren.created_at.replace(tzinfo=timezone.utc)
            pending_days = (now_utc - created_tz).days
            if pending_days > 7:
                risk_points += 20
                triggered_rules.append({
                    "rule_id": "RULE_STALE_RENEWAL",
                    "severity": "HIGH",
                    "title": f"Renewal Request Stalled ({pending_days} days)",
                    "explanation": f"Renewal request submitted {pending_days} days ago remains pending without official decision.",
                    "action": "Assign reviewing officer to expedite renewal decision"
                })

        # Priority Level Assessment
        if risk_points >= 40:
            priority = "HIGH"
        elif risk_points >= 15:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        return {
            "fdr_id": fdr.id,
            "fdr_number": fdr.fdr_number,
            "bank_name": fdr.bank_name,
            "branch_name": fdr.branch_name,
            "principal_amount": float(fdr.principal_amount),
            "status": fdr.status.value,
            "maturity_date": fdr.maturity_date.isoformat(),
            "days_left": days_left,
            "priority": priority,
            "risk_score": min(100, risk_points),
            "triggered_rules": triggered_rules,
            "has_discrepancy": fdr.has_discrepancy,
            "doc_count": doc_count
        }

    @classmethod
    def get_radar_summary(cls, db: Session, user: User) -> Dict[str, Any]:
        query = db.query(FDRRecord)
        if user.role == UserRole.INSTITUTION_USER and user.institution_id:
            query = query.filter(FDRRecord.institution_id == user.institution_id)

        all_fdrs = query.all()

        # Batch prefetch to avoid N+1 queries across large datasets
        doc_fdr_ids = set(r[0] for r in db.query(FDRDocument.fdr_id).distinct().all())
        all_pending_renewals = db.query(RenewalRequest).filter(
            RenewalRequest.status == RequestStatus.PENDING
        ).all()
        renewals_by_fdr = defaultdict(list)
        for ren in all_pending_renewals:
            renewals_by_fdr[ren.fdr_id].append(ren)

        items = [
            cls.analyze_fdr(f, db=None, doc_fdr_ids=doc_fdr_ids, renewals_by_fdr=renewals_by_fdr)
            for f in all_fdrs
        ]

        high_priority = [i for i in items if i["priority"] == "HIGH"]
        medium_priority = [i for i in items if i["priority"] == "MEDIUM"]
        low_priority = [i for i in items if i["priority"] == "LOW"]

        return {
            "total_evaluated": len(items),
            "high_count": len(high_priority),
            "medium_count": len(medium_priority),
            "low_count": len(low_priority),
            "discrepancy_count": sum(1 for i in items if i["has_discrepancy"]),
            "items": sorted(items, key=lambda x: x["risk_score"], reverse=True)
        }

class ConsistencyCheckerEngine:
    """
    Evaluates field integrity, document consistency, and date boundaries.
    """
    @staticmethod
    def run_checks(db: Session, user: User) -> Dict[str, Any]:
        query = db.query(FDRRecord)
        if user.role == UserRole.INSTITUTION_USER and user.institution_id:
            query = query.filter(FDRRecord.institution_id == user.institution_id)

        fdrs = query.all()
        # Batch prefetch document IDs to avoid N+1 queries
        doc_fdr_ids = set(r[0] for r in db.query(FDRDocument.fdr_id).distinct().all())
        inconsistencies: List[Dict[str, Any]] = []

        for fdr in fdrs:
            # 1. Date consistency
            if fdr.maturity_date <= fdr.issue_date:
                inconsistencies.append({
                    "id": f"{fdr.id}-DATE",
                    "fdr_id": fdr.id,
                    "fdr_number": fdr.fdr_number,
                    "bank_name": fdr.bank_name,
                    "field": "maturity_date",
                    "severity": "CRITICAL",
                    "issue_type": "Invalid Date Boundary",
                    "description": f"Maturity date ({fdr.maturity_date}) is on or before issue date ({fdr.issue_date}).",
                    "recommended_action": "Correct date parameters in FDR register"
                })

            # 2. Minimum tenure consistency
            tenure_days = (fdr.maturity_date - fdr.issue_date).days
            if tenure_days < 90:
                inconsistencies.append({
                    "id": f"{fdr.id}-TENURE",
                    "fdr_id": fdr.id,
                    "fdr_number": fdr.fdr_number,
                    "bank_name": fdr.bank_name,
                    "field": "issue_date / maturity_date",
                    "severity": "MEDIUM",
                    "issue_type": "Unusually Short Tenure",
                    "description": f"Tenure is only {tenure_days} days. Regulatory security deposits typically require minimum 1-year tenure.",
                    "recommended_action": "Verify compliance tenure requirement with issuing institution"
                })

            # 3. Missing Branch Details
            if not fdr.branch_name or not fdr.branch_name.strip():
                inconsistencies.append({
                    "id": f"{fdr.id}-BRANCH",
                    "fdr_id": fdr.id,
                    "fdr_number": fdr.fdr_number,
                    "bank_name": fdr.bank_name,
                    "field": "branch_name",
                    "severity": "LOW",
                    "issue_type": "Missing Branch Information",
                    "description": "Specific issuing branch name is not recorded.",
                    "recommended_action": "Update branch name for complete bank audit trail"
                })

            # 4. Document Verification Status (Batch check)
            has_doc = fdr.id in doc_fdr_ids
            if not has_doc and fdr.status not in (FDRStatus.DRAFT, FDRStatus.RELEASED):
                inconsistencies.append({
                    "id": f"{fdr.id}-DOC",
                    "fdr_id": fdr.id,
                    "fdr_number": fdr.fdr_number,
                    "bank_name": fdr.bank_name,
                    "field": "documents",
                    "severity": "HIGH",
                    "issue_type": "Unverified Without Physical Receipt",
                    "description": "Active/submitted deposit has no supporting scanned receipt or deposit voucher attached.",
                    "recommended_action": "Upload scanned fixed deposit receipt"
                })

            # 5. Active Discrepancy Flag
            if fdr.has_discrepancy:
                inconsistencies.append({
                    "id": f"{fdr.id}-DISCREPANCY",
                    "fdr_id": fdr.id,
                    "fdr_number": fdr.fdr_number,
                    "bank_name": fdr.bank_name,
                    "field": "discrepancy_notes",
                    "severity": "CRITICAL",
                    "issue_type": "Flagged Field Mismatch",
                    "description": fdr.discrepancy_notes or "Discrepancy identified between recorded values and supporting documents.",
                    "recommended_action": "Perform manual review against physical document"
                })

        return {
            "disclaimer": "Automated administrative consistency checks only. Passing checks does not constitute official commercial bank authentication.",
            "total_records_checked": len(fdrs),
            "inconsistency_count": len(inconsistencies),
            "items": inconsistencies
        }

class LifecycleChainEngine:
    """
    Constructs a traceable relationship chain of events:
    FDR Creation -> Document Upload -> Verification -> Renewal Requests -> Decision -> Release
    """
    @staticmethod
    def get_fdr_chain(db: Session, fdr_id: str) -> Dict[str, Any]:
        fdr = db.query(FDRRecord).filter(FDRRecord.id == fdr_id).first()
        if not fdr:
            return {"error": "FDR not found"}

        events = []

        # 1. Creation Event
        events.append({
            "stage": "CREATION",
            "title": "FDR Record Registered",
            "timestamp": fdr.created_at.isoformat(),
            "status": "COMPLETED",
            "actor": "FDR Officer / System",
            "details": f"Registered deposit #{fdr.fdr_number} for Rs. {float(fdr.principal_amount):,.2f} at {fdr.bank_name}."
        })

        # 2. Document Events
        docs = db.query(FDRDocument).filter(FDRDocument.fdr_id == fdr.id).all()
        for doc in docs:
            events.append({
                "stage": "DOCUMENT_UPLOAD",
                "title": f"Document Uploaded: {doc.document_type.value}",
                "timestamp": doc.created_at.isoformat(),
                "status": doc.ocr_status,
                "actor": "Institution User",
                "details": f"Uploaded '{doc.file_name}' ({doc.file_size_bytes} bytes). OCR Status: {doc.ocr_status}."
            })

        # 3. Verification Checks
        checks = db.query(VerificationCheck).filter(VerificationCheck.fdr_id == fdr.id).all()
        if checks:
            pass_count = sum(1 for c in checks if c.outcome == VerificationOutcome.PASSED)
            fail_count = sum(1 for c in checks if c.outcome == VerificationOutcome.FAILED)
            events.append({
                "stage": "VERIFICATION",
                "title": f"Automated Verification Suite ({len(checks)} checks)",
                "timestamp": checks[-1].created_at.isoformat(),
                "status": fdr.verification_status.value,
                "actor": "System Verification Engine",
                "details": f"{pass_count} passed, {fail_count} failed. Overall outcome: {fdr.verification_status.value}."
            })

        # 4. Renewal Requests
        renewals = db.query(RenewalRequest).filter(RenewalRequest.fdr_id == fdr.id).all()
        for ren in renewals:
            events.append({
                "stage": "RENEWAL",
                "title": f"Renewal Request ({ren.status.value})",
                "timestamp": ren.created_at.isoformat(),
                "status": ren.status.value,
                "actor": ren.requested_by.email if ren.requested_by else "Institution Officer",
                "details": f"Requested extension to {ren.new_maturity_date}. Rationale: {ren.rationale}"
            })

        # 5. Release Requests
        releases = db.query(ReleaseRequest).filter(ReleaseRequest.fdr_id == fdr.id).all()
        for rel in releases:
            events.append({
                "stage": "RELEASE",
                "title": f"Release Request ({rel.status.value})",
                "timestamp": rel.created_at.isoformat(),
                "status": rel.status.value,
                "actor": rel.requested_by.email if rel.requested_by else "Institution Officer",
                "details": f"Clearance Ref: {rel.clearance_reference}. Rationale: {rel.rationale}"
            })

        # 6. Review Decisions
        decisions = db.query(ReviewDecision).filter(ReviewDecision.fdr_id == fdr.id).all()
        for dec in decisions:
            events.append({
                "stage": "REVIEW_DECISION",
                "title": f"Official Decision: {dec.decision_type}",
                "timestamp": dec.created_at.isoformat(),
                "status": dec.new_status.value,
                "actor": dec.reviewer_id or "Reviewing Official",
                "details": f"Transitioned from {dec.previous_status.value} to {dec.new_status.value}. Reason: {dec.reason}"
            })

        # Sort timeline chronologically
        events.sort(key=lambda x: x["timestamp"])

        return {
            "fdr_id": fdr.id,
            "fdr_number": fdr.fdr_number,
            "bank_name": fdr.bank_name,
            "principal_amount": float(fdr.principal_amount),
            "current_status": fdr.status.value,
            "issue_date": fdr.issue_date.isoformat(),
            "maturity_date": fdr.maturity_date.isoformat(),
            "timeline_events": events
        }

    @classmethod
    def get_all_chains_summary(cls, db: Session, user: User, limit: int = 20) -> List[Dict[str, Any]]:
        query = db.query(FDRRecord)
        if user.role == UserRole.INSTITUTION_USER and user.institution_id:
            query = query.filter(FDRRecord.institution_id == user.institution_id)
        fdrs = query.order_by(desc(FDRRecord.created_at)).limit(limit).all()
        return [cls.get_fdr_chain(db, f.id) for f in fdrs]

class MaturityCalendarEngine:
    """
    Categorizes FDRs into actionable maturity countdown buckets.
    """
    @staticmethod
    def get_calendar_buckets(db: Session, user: User) -> Dict[str, Any]:
        query = db.query(FDRRecord)
        if user.role == UserRole.INSTITUTION_USER and user.institution_id:
            query = query.filter(FDRRecord.institution_id == user.institution_id)

        all_fdrs = query.all()
        today = date.today()

        expired = []
        within_7 = []
        within_15 = []
        within_30 = []
        future = []

        for fdr in all_fdrs:
            days = (fdr.maturity_date - today).days
            item = {
                "id": fdr.id,
                "fdr_number": fdr.fdr_number,
                "bank_name": fdr.bank_name,
                "principal_amount": float(fdr.principal_amount),
                "status": fdr.status.value,
                "maturity_date": fdr.maturity_date.isoformat(),
                "days_left": days,
                "has_discrepancy": fdr.has_discrepancy
            }

            if days < 0:
                expired.append(item)
            elif days <= 7:
                within_7.append(item)
            elif days <= 15:
                within_15.append(item)
            elif days <= 30:
                within_30.append(item)
            else:
                future.append(item)

        return {
            "as_of_date": today.isoformat(),
            "summary": {
                "total_records": len(all_fdrs),
                "expired_count": len(expired),
                "within_7_days_count": len(within_7),
                "within_15_days_count": len(within_15),
                "within_30_days_count": len(within_30),
                "future_count": len(future)
            },
            "buckets": {
                "expired": expired,
                "within_7_days": within_7,
                "within_15_days": within_15,
                "within_30_days": within_30,
                "future": future
            }
        }

class BottleneckMonitorEngine:
    """
    Tracks workflow review delays, pending queues, and SLA threshold breaches.
    """
    @staticmethod
    def get_bottlenecks(db: Session) -> Dict[str, Any]:
        now_utc = datetime.now(timezone.utc)

        # 1. Unverified or Submitted FDRs pending review
        submitted_fdrs = db.query(FDRRecord).filter(
            FDRRecord.status.in_([FDRStatus.SUBMITTED, FDRStatus.UNDER_REVIEW])
        ).all()

        fdr_bottlenecks = []
        for f in submitted_fdrs:
            created_tz = f.created_at if f.created_at.tzinfo else f.created_at.replace(tzinfo=timezone.utc)
            pending_days = (now_utc - created_tz).days
            if pending_days >= 3:
                fdr_bottlenecks.append({
                    "id": f.id,
                    "fdr_number": f.fdr_number,
                    "bank_name": f.bank_name,
                    "type": "INITIAL_VERIFICATION",
                    "status": f.status.value,
                    "pending_days": pending_days,
                    "responsible_role": "Reviewing Official / Verifier",
                    "action_required": "Perform verification check & update review queue"
                })

        # 2. Pending Renewal Requests
        renewals = db.query(RenewalRequest).filter(
            RenewalRequest.status == RequestStatus.PENDING
        ).all()

        renewal_bottlenecks = []
        for r in renewals:
            created_tz = r.created_at if r.created_at.tzinfo else r.created_at.replace(tzinfo=timezone.utc)
            pending_days = (now_utc - created_tz).days
            if pending_days >= 3:
                fdr_rec = db.query(FDRRecord).filter(FDRRecord.id == r.fdr_id).first()
                renewal_bottlenecks.append({
                    "id": r.id,
                    "fdr_id": r.fdr_id,
                    "fdr_number": fdr_rec.fdr_number if fdr_rec else "N/A",
                    "bank_name": fdr_rec.bank_name if fdr_rec else "N/A",
                    "type": "RENEWAL_APPROVAL",
                    "status": r.status.value,
                    "pending_days": pending_days,
                    "responsible_role": "Reviewing Official / Super Admin",
                    "action_required": "Approve renewal extension or request additional documentation"
                })

        # 3. Pending Release Requests
        releases = db.query(ReleaseRequest).filter(
            ReleaseRequest.status == RequestStatus.PENDING
        ).all()

        release_bottlenecks = []
        for rel in releases:
            created_tz = rel.created_at if rel.created_at.tzinfo else rel.created_at.replace(tzinfo=timezone.utc)
            pending_days = (now_utc - created_tz).days
            if pending_days >= 3:
                fdr_rec = db.query(FDRRecord).filter(FDRRecord.id == rel.fdr_id).first()
                release_bottlenecks.append({
                    "id": rel.id,
                    "fdr_id": rel.fdr_id,
                    "fdr_number": fdr_rec.fdr_number if fdr_rec else "N/A",
                    "bank_name": fdr_rec.bank_name if fdr_rec else "N/A",
                    "type": "RELEASE_APPROVAL",
                    "status": rel.status.value,
                    "pending_days": pending_days,
                    "responsible_role": "Super Admin / Clearance Authority",
                    "action_required": "Validate clearance reference & grant deposit release"
                })

        all_bottlenecks = fdr_bottlenecks + renewal_bottlenecks + release_bottlenecks
        all_bottlenecks.sort(key=lambda x: x["pending_days"], reverse=True)

        return {
            "total_stalled_items": len(all_bottlenecks),
            "verification_queue_pending": len(submitted_fdrs),
            "renewal_requests_pending": len(renewals),
            "release_requests_pending": len(releases),
            "critical_breaches_count": sum(1 for b in all_bottlenecks if b["pending_days"] >= 7),
            "items": all_bottlenecks
        }
