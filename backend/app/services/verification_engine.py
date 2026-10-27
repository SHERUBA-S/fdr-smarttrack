from datetime import date
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.fdr import FDRRecord, FDRDocument, ExtractedDocumentField, VerificationCheck
from app.models.enums import VerificationOutcome, SeverityLevel, FDRStatus

class VerificationEngine:
    """
    Transparent Verification Engine combining deterministic integrity rules
    and auditable discrepancy reporting.
    """
    EXTERNAL_VERIFICATION_DISCLAIMER = (
        "External bank authenticity verification has not been performed. "
        "A document that passes mathematical and optical field validation is not "
        "automatically a genuine bank-issued FDR. Actual bank verification requires "
        "an authorized direct bank API integration or physical confirmation."
    )

    @classmethod
    def run_all_checks(cls, db: Session, fdr: FDRRecord) -> List[VerificationCheck]:
        """Execute full verification suite on an FDR record."""
        # Clear existing verification checks for fresh run
        db.query(VerificationCheck).filter(VerificationCheck.fdr_id == fdr.id).delete()
        
        checks: List[VerificationCheck] = []
        has_critical_or_fail = False
        discrepancy_reasons = []

        # Rule 1: Required Fields
        req_missing = []
        if not fdr.fdr_number: req_missing.append("fdr_number")
        if not fdr.bank_name: req_missing.append("bank_name")
        if not fdr.principal_amount: req_missing.append("principal_amount")
        if not fdr.issue_date: req_missing.append("issue_date")
        if not fdr.maturity_date: req_missing.append("maturity_date")
        
        if req_missing:
            c = VerificationCheck(
                fdr_id=fdr.id,
                check_name="Required Fields Completeness",
                outcome=VerificationOutcome.FAILED,
                severity=SeverityLevel.CRITICAL,
                evidence=f"Missing fields: {', '.join(req_missing)}",
                explanation="One or more mandatory regulatory fields are blank or null.",
                recommended_action="Update record with all mandatory fields before submitting for review.",
                requires_human_review=True
            )
            has_critical_or_fail = True
            discrepancy_reasons.append("Mandatory fields missing")
        else:
            c = VerificationCheck(
                fdr_id=fdr.id,
                check_name="Required Fields Completeness",
                outcome=VerificationOutcome.PASSED,
                severity=SeverityLevel.INFO,
                evidence="All core fields present (FDR number, bank, principal, issue date, maturity date).",
                explanation="All required fields meet standard data schema requirements.",
                recommended_action="No action required.",
                requires_human_review=False
            )
        checks.append(c)

        # Rule 2: Date Sequence Validation (Maturity > Issue)
        if fdr.issue_date and fdr.maturity_date:
            if fdr.maturity_date <= fdr.issue_date:
                c = VerificationCheck(
                    fdr_id=fdr.id,
                    check_name="Chronological Date Sequence",
                    outcome=VerificationOutcome.FAILED,
                    severity=SeverityLevel.CRITICAL,
                    evidence=f"Issue Date: {fdr.issue_date} >= Maturity Date: {fdr.maturity_date}",
                    explanation="A Fixed Deposit Receipt maturity date cannot be equal to or earlier than its issue date.",
                    recommended_action="Correct the issue or maturity date according to the physical receipt.",
                    requires_human_review=True
                )
                has_critical_or_fail = True
                discrepancy_reasons.append("Invalid date chronological sequence")
            elif (fdr.maturity_date - fdr.issue_date).days < 90:
                c = VerificationCheck(
                    fdr_id=fdr.id,
                    check_name="Tenure Threshold Check",
                    outcome=VerificationOutcome.WARNING,
                    severity=SeverityLevel.MEDIUM,
                    evidence=f"Tenure is {(fdr.maturity_date - fdr.issue_date).days} days (< 90 days)",
                    explanation="Security deposits typically have a minimum statutory tenure of 90 days or 1 year.",
                    recommended_action="Verify if a short-term FDR meets regulatory deposit requirements.",
                    requires_human_review=True
                )
                checks.append(c)
            else:
                c = VerificationCheck(
                    fdr_id=fdr.id,
                    check_name="Chronological Date Sequence",
                    outcome=VerificationOutcome.PASSED,
                    severity=SeverityLevel.INFO,
                    evidence=f"Tenure: {(fdr.maturity_date - fdr.issue_date).days} days ({fdr.issue_date} to {fdr.maturity_date})",
                    explanation="Maturity date is strictly after issue date within valid bounds.",
                    recommended_action="No action required.",
                    requires_human_review=False
                )
            checks.append(c)

        # Rule 3: Amount Validation
        if fdr.principal_amount <= Decimal("0"):
            c = VerificationCheck(
                fdr_id=fdr.id,
                check_name="Principal Amount Range",
                outcome=VerificationOutcome.FAILED,
                severity=SeverityLevel.CRITICAL,
                evidence=f"Amount: ₹{fdr.principal_amount}",
                explanation="Principal amount must be strictly greater than zero.",
                recommended_action="Enter a valid positive financial deposit amount.",
                requires_human_review=True
            )
            has_critical_or_fail = True
            discrepancy_reasons.append("Invalid non-positive principal amount")
        elif fdr.principal_amount > Decimal("1000000000"):  # 100 Crore
            c = VerificationCheck(
                fdr_id=fdr.id,
                check_name="Principal Amount Range",
                outcome=VerificationOutcome.WARNING,
                severity=SeverityLevel.HIGH,
                evidence=f"Amount: ₹{fdr.principal_amount:,.2f}",
                explanation="Principal amount exceeds normal institutional ceiling (> ₹100 Crore). Requires administrative sign-off.",
                recommended_action="Reviewing official should double-check high value receipt against bank letter.",
                requires_human_review=True
            )
        else:
            c = VerificationCheck(
                fdr_id=fdr.id,
                check_name="Principal Amount Range",
                outcome=VerificationOutcome.PASSED,
                severity=SeverityLevel.INFO,
                evidence=f"Amount: ₹{fdr.principal_amount:,.2f}",
                explanation="Principal amount is within standard institutional security deposit parameters.",
                recommended_action="No action required.",
                requires_human_review=False
            )
        checks.append(c)

        # Rule 4: Duplicate Reference Check
        duplicate_query = db.query(FDRRecord).filter(
            FDRRecord.id != fdr.id,
            FDRRecord.fdr_number.ilike(fdr.fdr_number),
            FDRRecord.bank_name.ilike(fdr.bank_name)
        )
        duplicate = duplicate_query.first()
        if duplicate:
            c = VerificationCheck(
                fdr_id=fdr.id,
                check_name="Duplicate FDR Reference Detection",
                outcome=VerificationOutcome.FAILED,
                severity=SeverityLevel.CRITICAL,
                evidence=f"Matching FDR #{duplicate.fdr_number} at {duplicate.bank_name} already registered (Record ID: {duplicate.id}).",
                explanation="An active record with the identical FDR number and bank already exists in the system.",
                recommended_action="Check if this is an accidental duplicate submission or conflicting claim.",
                requires_human_review=True
            )
            has_critical_or_fail = True
            discrepancy_reasons.append(f"Duplicate FDR reference at {fdr.bank_name}")
        else:
            c = VerificationCheck(
                fdr_id=fdr.id,
                check_name="Duplicate FDR Reference Detection",
                outcome=VerificationOutcome.PASSED,
                severity=SeverityLevel.INFO,
                evidence="Reference number is unique for this issuing bank.",
                explanation="No conflicting records found with the same FDR number and bank.",
                recommended_action="No action required.",
                requires_human_review=False
            )
        checks.append(c)

        # Rule 5: Supporting Document Presence
        docs = db.query(FDRDocument).filter(FDRDocument.fdr_id == fdr.id).all()
        if not docs:
            c = VerificationCheck(
                fdr_id=fdr.id,
                check_name="Supporting Document Attachment",
                outcome=VerificationOutcome.WARNING,
                severity=SeverityLevel.HIGH,
                evidence="No document uploaded for this FDR record.",
                explanation="A scanned copy or original PDF receipt of the Fixed Deposit Receipt is required for verification.",
                recommended_action="Upload scanned PDF or high-resolution image of FDR receipt.",
                requires_human_review=True
            )
            discrepancy_reasons.append("Missing supporting FDR document")
        else:
            c = VerificationCheck(
                fdr_id=fdr.id,
                check_name="Supporting Document Attachment",
                outcome=VerificationOutcome.PASSED,
                severity=SeverityLevel.INFO,
                evidence=f"{len(docs)} document(s) attached: {', '.join(d.file_name for d in docs)}",
                explanation="Supporting document attachment requirement satisfied.",
                recommended_action="No action required.",
                requires_human_review=False
            )
        checks.append(c)

        # Rule 6: OCR Extracted Values vs Database Record Match
        mismatches = []
        for doc in docs:
            for field in doc.extracted_fields:
                ext_val = field.user_corrected_value if field.is_corrected else field.extracted_value
                if not ext_val:
                    continue
                if field.field_name == "fdr_number":
                    norm_ext = ext_val.replace(" ", "").upper()
                    norm_rec = fdr.fdr_number.replace(" ", "").upper()
                    if norm_ext != norm_rec:
                        mismatches.append(f"FDR Number (Doc: '{ext_val}' vs Record: '{fdr.fdr_number}')")
                elif field.field_name == "principal_amount":
                    try:
                        ext_amt = Decimal(ext_val.replace(",", "").strip())
                        if abs(ext_amt - fdr.principal_amount) > Decimal("0.01"):
                            mismatches.append(f"Principal (Doc: ₹{ext_amt:,.2f} vs Record: ₹{fdr.principal_amount:,.2f})")
                    except Exception:
                        pass

        if mismatches:
            c = VerificationCheck(
                fdr_id=fdr.id,
                check_name="Document Data vs Record Consistency",
                outcome=VerificationOutcome.WARNING,
                severity=SeverityLevel.HIGH,
                evidence=f"Discrepancies identified: {'; '.join(mismatches)}",
                explanation="Values extracted from the uploaded document do not match the form inputs entered into the database.",
                recommended_action="Review OCR extraction results side-by-side with document image and reconcile values.",
                requires_human_review=True
            )
            discrepancy_reasons.append("Document vs Database mismatch")
            checks.append(c)
        elif docs:
            c = VerificationCheck(
                fdr_id=fdr.id,
                check_name="Document Data vs Record Consistency",
                outcome=VerificationOutcome.PASSED,
                severity=SeverityLevel.INFO,
                evidence="Extracted document fields correlate with database values.",
                explanation="No discrepancies detected between OCR extracted fields and stored record.",
                recommended_action="No action required.",
                requires_human_review=False
            )
            checks.append(c)

        # Rule 7: External Bank Authenticity Disclaimer Check
        c_disclaimer = VerificationCheck(
            fdr_id=fdr.id,
            check_name="External Bank Authenticity Verification",
            outcome=VerificationOutcome.AWAITING_EXTERNAL,
            severity=SeverityLevel.INFO,
            evidence="Direct Core Banking System (CBS) integration is not configured.",
            explanation=cls.EXTERNAL_VERIFICATION_DISCLAIMER,
            recommended_action="Manual official verification or authorized bank confirmation letter required prior to release.",
            requires_human_review=True
        )
        checks.append(c_disclaimer)

        # Update record discrepancy state
        for chk in checks:
            db.add(chk)

        fdr.has_discrepancy = (len(discrepancy_reasons) > 0)
        fdr.discrepancy_notes = "; ".join(discrepancy_reasons) if discrepancy_reasons else None
        
        if has_critical_or_fail:
            fdr.verification_status = VerificationOutcome.FAILED
        elif fdr.has_discrepancy:
            fdr.verification_status = VerificationOutcome.WARNING
        else:
            fdr.verification_status = VerificationOutcome.AWAITING_EXTERNAL

        db.commit()
        db.refresh(fdr)
        return checks
