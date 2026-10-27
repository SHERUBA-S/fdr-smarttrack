from datetime import date, timedelta
from app.models.fdr import FDRRecord
from app.models.enums import FDRStatus

def test_renewal_workflow(client, admin_token, reviewer_token, db_session):
    # Find an approved FDR
    fdr = db_session.query(FDRRecord).filter(FDRRecord.status == FDRStatus.APPROVED).first()
    assert fdr is not None

    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    headers_reviewer = {"Authorization": f"Bearer {reviewer_token}"}

    new_maturity = fdr.maturity_date + timedelta(days=365)

    # 1. Submit Renewal Request
    res_req = client.post(f"/api/v1/workflows/fdrs/{fdr.id}/renew", headers=headers_admin, json={
        "new_maturity_date": str(new_maturity),
        "rationale": "Extension of deposit tenure for statutory compliance.",
        "supporting_doc_name": "Renewal_Affidavit.pdf"
    })
    assert res_req.status_code == 200
    assert res_req.json()["status"] == "PENDING"

    # Verify FDR status moved to Renewal Pending
    fdr_check = client.get(f"/api/v1/fdrs/{fdr.id}", headers=headers_admin).json()
    assert fdr_check["status"] == "Renewal Pending"

    # 2. Reviewer approves renewal
    res_decide = client.post(f"/api/v1/workflows/fdrs/{fdr.id}/decide", headers=headers_reviewer, json={
        "decision_type": "RENEW",
        "new_status": "Approved",
        "reason": "Renewal application verified and compliant with AICTE terms."
    })
    assert res_decide.status_code == 200
    assert res_decide.json()["new_status"] == "Approved"

    # Verify maturity date extended
    fdr_updated = client.get(f"/api/v1/fdrs/{fdr.id}", headers=headers_admin).json()
    assert fdr_updated["status"] == "Approved"
    assert fdr_updated["maturity_date"] == str(new_maturity)

def test_release_workflow(client, admin_token, reviewer_token, db_session):
    fdr = db_session.query(FDRRecord).filter(FDRRecord.status == FDRStatus.APPROVED).first()
    assert fdr is not None

    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    headers_reviewer = {"Authorization": f"Bearer {reviewer_token}"}

    # 1. Submit Release Request
    res_rel = client.post(f"/api/v1/workflows/fdrs/{fdr.id}/release", headers=headers_admin, json={
        "clearance_reference": "CLR-AICTE-NOC-2026-991",
        "rationale": "Completion of statutory security deposit period with full compliance.",
        "supporting_doc_name": "Clearance_Certificate.pdf"
    })
    assert res_rel.status_code == 200
    assert res_rel.json()["status"] == "PENDING"

    # 2. Reviewer approves release
    res_decide = client.post(f"/api/v1/workflows/fdrs/{fdr.id}/decide", headers=headers_reviewer, json={
        "decision_type": "RELEASE",
        "new_status": "Released",
        "reason": "Clearance reference verified against official registry."
    })
    assert res_decide.status_code == 200
    assert res_decide.json()["new_status"] == "Released"

def test_review_queue(client, reviewer_token):
    headers = {"Authorization": f"Bearer {reviewer_token}"}
    res = client.get("/api/v1/workflows/review-queue", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "items" in data
