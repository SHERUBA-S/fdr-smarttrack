import httpx
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_live_api():
    print("=== TASK 2: LIVE BACKEND API VERIFICATION ===")
    
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Health check
        res = client.get("/health")
        print(f"1. GET /health -> Status: {res.status_code}")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        health_data = res.json()
        assert health_data["status"] == "healthy"
        assert health_data["database"]["status"] == "connected"
        print(f"   Database: {health_data['database']['status']} ({health_data['database']['type']})")

        # 2. Authentication - invalid credentials test
        res = client.post("/auth/login", json={"email": "admin@smarttrack.gov.in", "password": "WrongPassword"})
        print(f"2. POST /auth/login (invalid password) -> Status: {res.status_code} (Expected 401)")
        assert res.status_code == 401

        # 3. Authentication - valid admin login
        res = client.post("/auth/login", json={"email": "admin@smarttrack.gov.in", "password": "AdminPassword@123"})
        print(f"3. POST /auth/login (Admin) -> Status: {res.status_code}")
        assert res.status_code == 200
        admin_token = res.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 4. GET /auth/me
        res = client.get("/auth/me", headers=admin_headers)
        print(f"4. GET /auth/me -> Status: {res.status_code}, User: {res.json()['email']} [{res.json()['role']}]")
        assert res.status_code == 200

        # 5. GET /dashboards/metrics
        res = client.get("/dashboards/metrics", headers=admin_headers)
        print(f"5. GET /dashboards/metrics -> Status: {res.status_code}")
        assert res.status_code == 200
        metrics = res.json()
        print(f"   Total FDRs: {metrics['total_fdrs']}, Recorded Principal: Rs. {float(metrics['total_recorded_principal']):,.2f}")
        print(f"   Discrepancy alerts: {metrics['records_with_discrepancies']}, Status buckets: {len(metrics['status_distribution'])}")

        # 6. GET /institutions/
        res = client.get("/institutions/?limit=5", headers=admin_headers)
        print(f"6. GET /institutions/ -> Status: {res.status_code}, Count: {len(res.json())}")
        assert res.status_code == 200
        assert len(res.json()) > 0
        first_inst = res.json()[0]

        # 7. GET /banks/
        res = client.get("/banks/", headers=admin_headers)
        print(f"7. GET /banks/ -> Status: {res.status_code}, Count: {len(res.json())}")
        assert res.status_code == 200
        assert len(res.json()) > 0

        # 8. GET /fdrs/ (pagination & filtering)
        res = client.get("/fdrs/?page=1&page_size=5&sort_by=created_at&sort_order=desc", headers=admin_headers)
        print(f"8. GET /fdrs/ -> Status: {res.status_code}, Total records: {res.json()['total']}")
        assert res.status_code == 200
        fdrs = res.json()["items"]
        assert len(fdrs) > 0
        first_fdr = fdrs[0]

        # 9. GET /fdrs/{id}
        res = client.get(f"/fdrs/{first_fdr['id']}", headers=admin_headers)
        print(f"9. GET /fdrs/{{id}} -> Status: {res.status_code}, FDR: {res.json()['fdr_number']}")
        assert res.status_code == 200
        assert res.json()["id"] == first_fdr["id"]

        # 10. POST /fdrs/ validation failure (invalid dates)
        res = client.post("/fdrs/", headers=admin_headers, json={
            "fdr_number": "INVALID/2026",
            "institution_id": first_inst["id"],
            "bank_name": "State Bank of India",
            "principal_amount": "500000.00",
            "issue_date": "2026-05-01",
            "maturity_date": "2026-04-01",  # Invalid maturity before issue!
            "purpose": "Test"
        })
        print(f"10. POST /fdrs/ (invalid maturity < issue) -> Status: {res.status_code} (Expected 422)")
        assert res.status_code == 422

        # 11. POST /fdrs/{id}/verify (trigger verification suite & ML anomaly scorer)
        res = client.post(f"/fdrs/{first_fdr['id']}/verify", headers=admin_headers)
        print(f"11. POST /fdrs/{{id}}/verify -> Status: {res.status_code}")
        assert res.status_code == 200
        verify_data = res.json()
        print(f"    Verification Status: {verify_data['verification_status']}, Anomaly Score: {verify_data['anomaly_score']}")

        # 12. GET /workflows/review-queue (Reviewer role test)
        res_rev = client.post("/auth/login", json={"email": "reviewer@smarttrack.gov.in", "password": "ReviewerPassword@123"})
        reviewer_token = res_rev.json()["access_token"]
        reviewer_headers = {"Authorization": f"Bearer {reviewer_token}"}
        res = client.get("/workflows/review-queue", headers=reviewer_headers)
        print(f"12. GET /workflows/review-queue -> Status: {res.status_code}, Items in queue: {res.json()['total']}")
        assert res.status_code == 200

        # 13. GET /notifications/
        res = client.get("/notifications/", headers=admin_headers)
        print(f"13. GET /notifications/ -> Status: {res.status_code}, Unread count: {res.json()['unread_count']}")
        assert res.status_code == 200

        # 14. GET /audit-logs/
        res = client.get("/audit-logs/?page=1&page_size=5", headers=admin_headers)
        print(f"14. GET /audit-logs/ -> Status: {res.status_code}, Total logs: {res.json()['total']}")
        assert res.status_code == 200

    print("\n=== ALL 14 LIVE BACKEND API ENDPOINTS VERIFIED AND WORKING ===")

if __name__ == "__main__":
    test_live_api()
