import random
import time
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.institution import Institution, Bank
from app.models.user import User
from app.models.fdr import FDRRecord, FDRDocument, ExtractedDocumentField, VerificationCheck
from app.models.workflow import RenewalRequest, ReleaseRequest, ReviewDecision
from app.models.notification import Notification
from app.models.audit import AuditLog
from app.models.setting import DatasetGenerationJob
from app.models.enums import UserRole, FDRStatus, VerificationOutcome, SeverityLevel, RequestStatus, DocumentType
from app.core.security import hash_password

STATES = [
    ("MH", "Maharashtra", ["Mumbai", "Pune", "Nagpur", "Nashik"]),
    ("DL", "Delhi", ["New Delhi", "North Delhi", "South Delhi"]),
    ("KA", "Karnataka", ["Bengaluru", "Mysuru", "Mangaluru", "Hubballi"]),
    ("TN", "Tamil Nadu", ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli"]),
    ("TS", "Telangana", ["Hyderabad", "Warangal", "Nizamabad"]),
    ("UP", "Uttar Pradesh", ["Lucknow", "Noida", "Kanpur", "Varanasi"]),
    ("GJ", "Gujarat", ["Ahmedabad", "Surat", "Vadodara", "Rajkot"]),
    ("WB", "West Bengal", ["Kolkata", "Howrah", "Durgapur"])
]

BANK_NAMES = [
    ("SBI", "State Bank of India", "SBIN"),
    ("PNB", "Punjab National Bank", "PUNB"),
    ("HDFC", "HDFC Bank", "HDFC"),
    ("ICICI", "ICICI Bank", "ICIC"),
    ("BOB", "Bank of Baroda", "BARB"),
    ("CANARA", "Canara Bank", "CNRB"),
    ("UNION", "Union Bank of India", "UBIN"),
    ("AXIS", "Axis Bank", "UTIB"),
    ("INDIAN", "Indian Bank", "IDIB"),
    ("KOTAK", "Kotak Mahindra Bank", "KKBK")
]

INST_PREFIXES = ["National Institute of Technology", "Government Polytechnic", "Indian Institute of Management", "Apex Engineering College", "St. Xavier Institute of Science", "Vidyapeeth Academy", "Global Institute of Technology", "Modern Arts and Commerce College", "Imperial College of Technology", "Presidency Institute of Polytechnic"]

def generate_synthetic_dataset(db: Session, mode: str = "DEMO", seed: int = 42) -> Dict[str, Any]:
    """
    Generate realistic synthetic dataset for testing and hackathon demonstration.
    mode: 'DEMO' (fast demo dataset) or 'FULL' (up to 20,000 FDRs).
    """
    random.seed(seed)
    start_time = time.time()

    # Determine counts based on mode
    if mode.upper() == "FULL":
        n_institutions = 2000
        n_banks = 100
        n_fdrs = 20000
        n_requests = 5000
        n_notifications = 10000
        n_audits = 25000
    else:  # DEMO mode
        n_institutions = 60
        n_banks = 15
        n_fdrs = 350
        n_requests = 60
        n_notifications = 150
        n_audits = 300

    job = DatasetGenerationJob(mode=mode, status="RUNNING")
    db.add(job)
    db.commit()

    today = date.today()

    # 1. Banks
    banks: List[Bank] = []
    for i in range(n_banks):
        base_code, base_name, prefix = BANK_NAMES[i % len(BANK_NAMES)]
        branch_name = f"{random.choice(STATES)[2][0]} Main Branch #{i+1}"
        b = Bank(
            code=f"{base_code}_{i+1:03d}",
            name=f"{base_name} ({branch_name})",
            branch=branch_name,
            ifsc_prefix=f"{prefix}0{random.randint(10000, 99999)}",
            is_active=True,
            is_synthetic=True
        )
        banks.append(b)
    db.bulk_save_objects(banks, return_defaults=True)
    db.commit()

    # Re-query banks to ensure IDs are populated
    saved_banks = db.query(Bank).filter(Bank.is_synthetic == True).all()

    # 2. Institutions
    institutions: List[Institution] = []
    for i in range(n_institutions):
        st_code, st_name, cities = random.choice(STATES)
        city = random.choice(cities)
        prefix = random.choice(INST_PREFIXES)
        inst = Institution(
            code=f"INST-{st_code}-{i+1:04d}",
            name=f"{prefix} {city} (Campus #{i+1})",
            state=st_name,
            city=city,
            contact_email=f"registrar.inst{i+1}@smarttrack-demo.edu.in",
            contact_phone=f"+91 9{random.randint(100000000, 999999999)}",
            is_active=True,
            is_synthetic=True
        )
        institutions.append(inst)
    db.bulk_save_objects(institutions, return_defaults=True)
    db.commit()

    saved_institutions = db.query(Institution).filter(Institution.is_synthetic == True).all()

    # 3. Create Sample Institution Users
    demo_inst_user = db.query(User).filter(User.email == "institution@smarttrack.gov.in").first()
    if not demo_inst_user and saved_institutions:
        demo_inst_user = User(
            email="institution@smarttrack.gov.in",
            full_name="Dr. S. K. Raman (Registrar)",
            hashed_password=hash_password("DemoPassword@123"),
            role=UserRole.INSTITUTION_USER,
            institution_id=saved_institutions[0].id,
            is_active=True,
            is_mfa_enabled=False
        )
        db.add(demo_inst_user)
        db.commit()

    # 4. FDR Records
    fdrs: List[FDRRecord] = []
    statuses = [
        FDRStatus.APPROVED,
        FDRStatus.SUBMITTED,
        FDRStatus.UNDER_REVIEW,
        FDRStatus.RENEWAL_PENDING,
        FDRStatus.RELEASE_REQUESTED,
        FDRStatus.RELEASED,
        FDRStatus.EXPIRED,
        FDRStatus.ADDITIONAL_INFO_REQUIRED
    ]
    status_weights = [0.45, 0.15, 0.10, 0.10, 0.08, 0.05, 0.04, 0.03]

    amount_choices = [
        Decimal("250000.00"), Decimal("500000.00"), Decimal("1000000.00"),
        Decimal("1500000.00"), Decimal("2500000.00"), Decimal("5000000.00"),
        Decimal("10000000.00"), Decimal("20000000.00")
    ]

    for i in range(n_fdrs):
        inst = random.choice(saved_institutions)
        bank = random.choice(saved_banks)
        st = random.choices(statuses, weights=status_weights)[0]

        # Issue date between 3 years ago and 1 month ago
        issue_offset = random.randint(30, 1100)
        issue_d = today - timedelta(days=issue_offset)

        # Maturity date: some upcoming in 7d, 30d, 90d, some overdue, some far future
        maturity_bucket = random.choice(["URGENT_7D", "UPCOMING_30D", "UPCOMING_90D", "OVERDUE", "NORMAL_FUTURE"])
        if maturity_bucket == "URGENT_7D":
            maturity_d = today + timedelta(days=random.randint(1, 7))
        elif maturity_bucket == "UPCOMING_30D":
            maturity_d = today + timedelta(days=random.randint(8, 30))
        elif maturity_bucket == "UPCOMING_90D":
            maturity_d = today + timedelta(days=random.randint(31, 90))
        elif maturity_bucket == "OVERDUE":
            maturity_d = today - timedelta(days=random.randint(5, 120))
            if st not in [FDRStatus.RELEASED, FDRStatus.EXPIRED]:
                st = FDRStatus.APPROVED
        else:
            maturity_d = today + timedelta(days=random.randint(120, 1095))

        amt = random.choice(amount_choices)
        rate = Decimal(str(round(random.uniform(6.25, 8.15), 2)))

        # Intentional seeded edge cases for ~5% of records
        has_disc = False
        disc_notes = None
        if i % 20 == 0:
            has_disc = True
            disc_notes = "Extracted document value does not match recorded principal amount."

        fdr = FDRRecord(
            fdr_number=f"FDR/{bank.code.split('_')[0]}/{2024 + (i % 3)}/{100000 + i}",
            institution_id=inst.id,
            bank_id=bank.id,
            bank_name=bank.name,
            branch_name=bank.branch,
            principal_amount=amt,
            currency="INR",
            interest_rate=rate,
            issue_date=issue_d,
            maturity_date=maturity_d,
            purpose="AICTE Regulatory Approval Security Deposit",
            status=st,
            verification_status=VerificationOutcome.PASSED if not has_disc else VerificationOutcome.WARNING,
            has_discrepancy=has_disc,
            discrepancy_notes=disc_notes,
            anomaly_score=0.85 if has_disc else 0.08,
            is_synthetic=True
        )
        fdrs.append(fdr)

    db.bulk_save_objects(fdrs, return_defaults=True)
    db.commit()

    saved_fdrs = db.query(FDRRecord).filter(FDRRecord.is_synthetic == True).limit(min(n_fdrs, 500)).all()

    # 5. Attach synthetic documents and verification checks to representative subset
    docs: List[FDRDocument] = []
    checks: List[VerificationCheck] = []
    sample_fdrs = saved_fdrs[:min(len(saved_fdrs), 100)]

    for fdr in sample_fdrs:
        doc = FDRDocument(
            fdr_id=fdr.id,
            file_path=f"data/uploads/synthetic_fdr_{fdr.id}.pdf",
            file_name=f"FDR_Receipt_{fdr.fdr_number.replace('/', '_')}.pdf",
            file_size_bytes=random.randint(150000, 850000),
            mime_type="application/pdf",
            file_hash=f"hash_{fdr.id[:16]}_{random.randint(1000, 9999)}",
            document_type=DocumentType.FDR_RECEIPT,
            ocr_status="COMPLETED",
            raw_ocr_text=f"FIXED DEPOSIT RECEIPT\nBank: {fdr.bank_name}\nReceipt No: {fdr.fdr_number}\nAmount: Rs. {fdr.principal_amount}\nIssue Date: {fdr.issue_date}\nMaturity Date: {fdr.maturity_date}\nInterest Rate: {fdr.interest_rate}%"
        )
        docs.append(doc)

        c1 = VerificationCheck(
            fdr_id=fdr.id,
            check_name="Required Fields Completeness",
            outcome=VerificationOutcome.PASSED,
            severity=SeverityLevel.INFO,
            explanation="All core regulatory fields are present.",
            requires_human_review=False
        )
        c2 = VerificationCheck(
            fdr_id=fdr.id,
            check_name="Chronological Date Sequence",
            outcome=VerificationOutcome.PASSED,
            severity=SeverityLevel.INFO,
            explanation=f"Maturity date ({fdr.maturity_date}) is validly after issue date ({fdr.issue_date}).",
            requires_human_review=False
        )
        c3 = VerificationCheck(
            fdr_id=fdr.id,
            check_name="External Bank Authenticity Verification",
            outcome=VerificationOutcome.AWAITING_EXTERNAL,
            severity=SeverityLevel.INFO,
            explanation="External bank authenticity verification has not been performed.",
            recommended_action="Physical verification or authorized bank confirmation letter required.",
            requires_human_review=True
        )
        checks.extend([c1, c2, c3])

    db.bulk_save_objects(docs)
    db.bulk_save_objects(checks)
    db.commit()

    # 6. Workflow requests (Renewal & Release)
    renewals: List[RenewalRequest] = []
    releases: List[ReleaseRequest] = []
    renewal_candidates = [f for f in saved_fdrs if f.status == FDRStatus.RENEWAL_PENDING][:n_requests]
    release_candidates = [f for f in saved_fdrs if f.status == FDRStatus.RELEASE_REQUESTED][:n_requests]

    for fdr in renewal_candidates:
        r = RenewalRequest(
            fdr_id=fdr.id,
            new_maturity_date=fdr.maturity_date + timedelta(days=365),
            status=RequestStatus.PENDING,
            rationale="Extension of security deposit for statutory AICTE affiliation compliance for academic cycle 2026-2027.",
            supporting_doc_name=f"Renewal_Letter_{fdr.fdr_number.replace('/', '_')}.pdf"
        )
        renewals.append(r)

    for fdr in release_candidates:
        rel = ReleaseRequest(
            fdr_id=fdr.id,
            clearance_reference=f"CLR-AICTE-2026-{random.randint(10000, 99999)}",
            status=RequestStatus.PENDING,
            rationale="Release of security deposit following successful completion of institutional endowment obligations.",
            supporting_doc_name=f"Clearance_NOC_{fdr.fdr_number.replace('/', '_')}.pdf"
        )
        releases.append(rel)

    db.bulk_save_objects(renewals)
    db.bulk_save_objects(releases)
    db.commit()

    # Complete job record
    elapsed = time.time() - start_time
    job.status = "COMPLETED"
    job.total_institutions = n_institutions
    job.total_fdrs = n_fdrs
    job.duration_seconds = round(elapsed, 2)
    job.completed_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "status": "SUCCESS",
        "mode": mode,
        "institutions_created": n_institutions,
        "banks_created": n_banks,
        "fdrs_created": n_fdrs,
        "renewals_created": len(renewals),
        "releases_created": len(releases),
        "duration_seconds": round(elapsed, 2)
    }
