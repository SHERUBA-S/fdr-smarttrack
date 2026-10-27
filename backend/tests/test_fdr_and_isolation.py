from datetime import date, timedelta
from app.models.institution import Institution
from app.models.fdr import FDRRecord

def test_fdr_date_validation_rejected(client, institution_token, db_session):
    inst = db_session.query(Institution).first()
    headers = {"Authorization": f"Bearer {institution_token}"}
    
    # Attempt creating FDR with maturity date before issue date
    res = client.post("/api/v1/fdrs/", headers=headers, json={
        "fdr_number": "TEST/INV/2026/01",
        "institution_id": inst.id,
        "bank_name": "State Bank of India",
        "principal_amount": "500000.00",
        "issue_date": str(date.today()),
        "maturity_date": str(date.today() - timedelta(days=30)), # Invalid!
        "purpose": "Test Security Deposit"
    })
    assert res.status_code == 422  # Pydantic validation failure

def test_institution_data_isolation(client, db_session):
    # Find two distinct institutions
    institutions = db_session.query(Institution).limit(2).all()
    assert len(institutions) >= 2
    inst_a, inst_b = institutions[0], institutions[1]

    # Login as institution user bound to inst_a
    res_inst = client.post("/api/v1/auth/login", json={
        "email": "institution@smarttrack.gov.in",
        "password": "DemoPassword@123"
    })
    token = res_inst.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Query FDRs for inst_b directly via institution user
    fdr_b = db_session.query(FDRRecord).filter(FDRRecord.institution_id == inst_b.id).first()
    if fdr_b:
        res = client.get(f"/api/v1/fdrs/{fdr_b.id}", headers=headers)
        # Should be forbidden 403 because user belongs to inst_a
        assert res.status_code == 403

def test_fdr_creation_and_automatic_verification(client, admin_token, db_session):
    inst = db_session.query(Institution).first()
    headers = {"Authorization": f"Bearer {admin_token}"}

    res = client.post("/api/v1/fdrs/", headers=headers, json={
        "fdr_number": "TEST/SBI/2026/889900",
        "institution_id": inst.id,
        "bank_name": "State Bank of India",
        "branch_name": "New Delhi Main",
        "principal_amount": "1250000.00",
        "interest_rate": "7.15",
        "issue_date": str(date.today() - timedelta(days=180)),
        "maturity_date": str(date.today() + timedelta(days=365)),
        "purpose": "AICTE Approval Guarantee"
    })
    assert res.status_code == 201
    fdr_data = res.json()
    assert fdr_data["fdr_number"] == "TEST/SBI/2026/889900"
    assert fdr_data["status"] == "Submitted"
    assert "verification_checks" in fdr_data
    assert len(fdr_data["verification_checks"]) > 0
