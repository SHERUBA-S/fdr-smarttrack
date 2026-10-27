"""
Verification script: Submit a fictional FDR record through the API,
verify its insertion into PostgreSQL directly with psycopg/SQLAlchemy,
and verify its retrieval through the REST API.
"""
import os
import sys
from decimal import Decimal
import httpx
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/fdr_smarttrack_db"
)
API_BASE = "http://127.0.0.1:8000/api/v1"

def run_fdr_flow_verification():
    print("=== STEP 1: AUTHENTICATING AS ADMIN ===")
    with httpx.Client(base_url=API_BASE, timeout=10.0) as client:
        login_resp = client.post("/auth/login", json={
            "email": "admin@smarttrack.gov.in",
            "password": "AdminPassword@123"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("   Admin authenticated successfully.")

        # Get an existing institution
        inst_resp = client.get("/institutions/?limit=1", headers=headers)
        assert inst_resp.status_code == 200
        inst = inst_resp.json()[0]
        print(f"   Using Institution: {inst['name']} (ID: {inst['id']})")

        print("\n=== STEP 2: SUBMITTING FICTIONAL FDR RECORD THROUGH API ===")
        test_fdr_payload = {
            "fdr_number": "TEST/VERIFY/2026/998811",
            "institution_id": inst["id"],
            "bank_name": "Canara Bank",
            "branch_name": "Koramangala 5th Block",
            "principal_amount": 1250000.00,
            "currency": "INR",
            "interest_rate": 7.25,
            "issue_date": "2026-03-01",
            "maturity_date": "2027-03-01",
            "purpose": "AICTE Statutory Compliance Guarantee"
        }
        create_resp = client.post("/fdrs/", headers=headers, json=test_fdr_payload)
        assert create_resp.status_code == 201, f"Create FDR failed ({create_resp.status_code}): {create_resp.text}"
        created_fdr = create_resp.json()
        fdr_id = created_fdr["id"]
        print(f"   API Response: 201 Created")
        print(f"   Assigned FDR ID: {fdr_id}")
        print(f"   FDR Number: {created_fdr['fdr_number']}")
        print(f"   Initial Status: {created_fdr['status']}")

        print("\n=== STEP 3: QUERYING POSTGRESQL DIRECTLY ON PORT 5433 ===")
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Query fdr_records table
            row = conn.execute(
                text("SELECT id, fdr_number, bank_name, principal_amount, status FROM fdr_records WHERE id = :id"),
                {"id": fdr_id}
            ).fetchone()
            assert row is not None, f"FDR {fdr_id} was NOT found in PostgreSQL table 'fdr_records'!"
            print(f"   Found in 'fdr_records' table:")
            print(f"   - Database ID: {row[0]}")
            print(f"   - FDR Number: {row[1]}")
            print(f"   - Bank Name: {row[2]}")
            print(f"   - Principal Amount: Rs. {float(row[3]):,.2f}")
            print(f"   - DB Status: {row[4]}")

            # Query fdrs view
            view_row = conn.execute(
                text("SELECT id, fdr_number FROM fdrs WHERE id = :id"),
                {"id": fdr_id}
            ).fetchone()
            assert view_row is not None, f"FDR {fdr_id} was NOT found in PostgreSQL view 'fdrs'!"
            print(f"   Found in 'fdrs' view: ID={view_row[0]}, Number={view_row[1]}")

        print("\n=== STEP 4: RETRIEVING CREATED RECORD VIA GET /fdrs/{id} API ===")
        get_resp = client.get(f"/fdrs/{fdr_id}", headers=headers)
        assert get_resp.status_code == 200, f"Retrieve failed: {get_resp.text}"
        fetched_fdr = get_resp.json()
        print(f"   Retrieved from API: {fetched_fdr['fdr_number']} (Status: {fetched_fdr['status']})")
        assert fetched_fdr["fdr_number"] == "TEST/VERIFY/2026/998811"
        assert float(fetched_fdr["principal_amount"]) == 1250000.00
        assert fetched_fdr["bank_name"] == "Canara Bank"

        print("\n=== STEP 5: VERIFYING AUDIT TRAIL LOGGED IN POSTGRESQL ===")
        with engine.connect() as conn:
            audit_row = conn.execute(
                text("SELECT id, action, entity_id, actor_email, created_at FROM audit_logs WHERE entity_id = :id"),
                {"id": fdr_id}
            ).fetchone()
            assert audit_row is not None, "Audit log was not recorded for FDR creation!"
            print(f"   Audit Log ID: {audit_row[0]}")
            print(f"   Action: {audit_row[1]} by {audit_row[3]}")

    print("\nSUCCESS: Complete flow verified from API submission -> PostgreSQL commit -> API retrieval!")

if __name__ == "__main__":
    run_fdr_flow_verification()
