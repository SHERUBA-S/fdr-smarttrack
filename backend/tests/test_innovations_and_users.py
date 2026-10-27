import pytest
from app.models.enums import UserRole

def test_user_management_and_registration(client, admin_token):
    auth_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 1. Register a new FDR Officer
    new_email = "test_fdr_officer_new@smarttrack.gov.in"
    reg_res = client.post("/api/v1/auth/register", json={
        "email": new_email,
        "full_name": "New FDR Officer",
        "password": "Password@123456",
        "role": "INSTITUTION_USER"
    })
    assert reg_res.status_code in [200, 400]  # 400 if already created in earlier run
    
    # 2. As admin, query users list
    users_res = client.get("/api/v1/users/", headers=auth_headers)
    assert users_res.status_code == 200
    users = users_res.json()
    assert isinstance(users, list)
    assert len(users) > 0
    
    # Ensure safe fields only: no password hash or tokens
    for u in users:
        assert "password" not in u
        assert "hashed_password" not in u
        assert "access_token" not in u
        assert "email" in u
        assert "role" in u
        assert "is_active" in u

    # 3. Non-admin cannot query users list
    user_login = client.post("/api/v1/auth/login", json={
        "email": new_email,
        "password": "Password@123456"
    })
    if user_login.status_code == 200 and not user_login.json().get("requires_mfa"):
        user_token = user_login.json()["access_token"]
        unauth_res = client.get("/api/v1/users/", headers={"Authorization": f"Bearer {user_token}"})
        assert unauth_res.status_code == 403


def test_explainable_risk_radar(client, admin_token):
    auth_headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/api/v1/fdrs/risk-radar", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_evaluated" in data
    assert "high_count" in data
    assert "medium_count" in data
    assert "low_count" in data
    assert "items" in data
    assert isinstance(data["items"], list)
    
    if len(data["items"]) > 0:
        first = data["items"][0]
        assert "fdr_id" in first
        assert "fdr_number" in first
        assert "priority" in first
        assert first["priority"] in ["HIGH", "MEDIUM", "LOW"]
        assert "triggered_rules" in first
        assert isinstance(first["triggered_rules"], list)
        assert "risk_score" in first


def test_document_consistency_checker(client, admin_token):
    auth_headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/api/v1/fdrs/consistency-checker", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_records_checked" in data
    assert "inconsistency_count" in data
    assert "disclaimer" in data
    assert "Automated administrative consistency checks only" in data["disclaimer"]
    assert "items" in data
    assert isinstance(data["items"], list)


def test_maturity_calendar(client, admin_token):
    auth_headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/api/v1/fdrs/maturity-calendar", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "as_of_date" in data
    assert "summary" in data
    assert "buckets" in data
    summary = data["summary"]
    assert "total_records" in summary
    assert "within_7_days_count" in summary
    assert "within_15_days_count" in summary
    assert "within_30_days_count" in summary
    buckets = data["buckets"]
    assert "within_7_days" in buckets
    assert "within_15_days" in buckets
    assert "within_30_days" in buckets


def test_lifecycle_chains(client, admin_token):
    auth_headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/api/v1/fdrs/lifecycle-chains", headers=auth_headers)
    assert res.status_code == 200
    chains = res.json()
    assert isinstance(chains, list)
    if len(chains) > 0:
        first_chain = chains[0]
        assert "fdr_id" in first_chain
        assert "fdr_number" in first_chain
        assert "bank_name" in first_chain
        assert "timeline_events" in first_chain
        assert isinstance(first_chain["timeline_events"], list)


def test_workflow_bottlenecks(client, admin_token):
    auth_headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/api/v1/workflows/bottlenecks", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_stalled_items" in data
    assert "verification_queue_pending" in data
    assert "renewal_requests_pending" in data
    assert "release_requests_pending" in data
    assert "critical_breaches_count" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_safe_csv_export(client, admin_token):
    auth_headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/api/v1/fdrs/export-csv", headers=auth_headers)
    assert res.status_code == 200
    assert "text/csv" in res.headers.get("content-type", "")
    content = res.text
    assert "FDR Reference Number" in content
    assert "Principal Amount (INR)" in content
    # Verify no unescaped spreadsheet formula injection characters at start of cells
    for line in content.splitlines()[1:]:
        cells = line.split(",")
        for c in cells:
            clean = c.strip('" ')
            if clean:
                assert not clean.startswith(("=", "+", "-", "@")) or clean.startswith("'")
