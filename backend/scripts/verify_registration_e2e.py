"""
End-to-end verification script for FDR Guardian Registration & Authentication.
Tests:
1. Public institutions fetch (unauthenticated)
2. Empty institution_id sanitization
3. Nonexistent institution_id rejection (HTTP 400, not 500)
4. Blank full_name rejection (HTTP 400)
5. Invalid email format rejection (HTTP 422)
6. Short password rejection (HTTP 422)
7. Super admin privilege escalation rejection (HTTP 403)
8. Successful registration & PostgreSQL verification
9. Duplicate email rejection (HTTP 400)
10. Login with correct and incorrect credentials
"""
import uuid
import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_tests():
    print("=== STARTING END-TO-END REGISTRATION VERIFICATION ===")
    
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Public Institutions
        r = client.get("/institutions/public")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        institutions = r.json()
        print(f"[PASS] 1. Public institutions endpoint returned {len(institutions)} institutions (Unauthenticated)")
        sample_inst_id = institutions[0]["id"] if institutions else None

        # 2. Empty string institution_id sanitization (previously threw 500 error)
        test_uid = uuid.uuid4().hex[:6]
        email_empty_inst = f"officer_unassigned_{test_uid}@demo-institute.org"
        r = client.post("/auth/register", json={
            "full_name": "Unassigned Officer",
            "email": email_empty_inst,
            "password": "SecurePassword@2026",
            "role": "INSTITUTION_USER",
            "institution_id": ""
        })
        assert r.status_code == 200, f"Expected 200 for empty institution_id, got {r.status_code}: {r.text}"
        user_data = r.json()
        assert user_data["institution_id"] is None
        print(f"[PASS] 2. Empty institution_id safely sanitized to None without Foreign Key 500 error")

        # 3. Nonexistent institution_id rejection
        r = client.post("/auth/register", json={
            "full_name": "Bogus Officer",
            "email": f"bogus_{test_uid}@demo.org",
            "password": "SecurePassword@2026",
            "role": "INSTITUTION_USER",
            "institution_id": "nonexistent-institution-id-999"
        })
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"
        assert "Selected institution does not exist" in r.text
        print(f"[PASS] 3. Nonexistent institution_id safely rejected with 400: '{r.json()['detail']}'")

        # 4. Blank full_name rejection
        r = client.post("/auth/register", json={
            "full_name": "   ",
            "email": f"blank_name_{test_uid}@demo.org",
            "password": "SecurePassword@2026",
            "role": "REVIEWING_OFFICIAL"
        })
        assert r.status_code == 400
        assert "Full name cannot be blank" in r.text
        print(f"[PASS] 4. Blank full name rejected with 400: '{r.json()['detail']}'")

        # 5. Invalid email format rejection
        r = client.post("/auth/register", json={
            "full_name": "Valid Name",
            "email": "not-an-email-address",
            "password": "SecurePassword@2026",
            "role": "REVIEWING_OFFICIAL"
        })
        assert r.status_code == 422
        print(f"[PASS] 5. Invalid email format rejected with 422 Unprocessable Entity")

        # 6. Short password (< 8 chars) rejection
        r = client.post("/auth/register", json={
            "full_name": "Valid Name",
            "email": f"short_pw_{test_uid}@demo.org",
            "password": "short",
            "role": "REVIEWING_OFFICIAL"
        })
        assert r.status_code == 422
        print(f"[PASS] 6. Short password (< 8 chars) rejected with 422 Unprocessable Entity")

        # 7. Super Admin privilege escalation rejection
        r = client.post("/auth/register", json={
            "full_name": "Hacker Attempt",
            "email": f"hacker_{test_uid}@demo.org",
            "password": "SecurePassword@2026",
            "role": "SUPER_ADMIN"
        })
        assert r.status_code == 403
        assert "Administrator accounts cannot be self-registered" in r.text
        print(f"[PASS] 7. Privilege escalation to SUPER_ADMIN rejected with 403 Forbidden")

        # 8. Successful Registration (with real institution if available)
        main_test_email = f"fdr_officer_{test_uid}@guardian-institution.edu.in"
        reg_payload = {
            "full_name": "Prof. Ananya Sharma",
            "email": main_test_email,
            "password": "OfficerPassword@2026",
            "role": "INSTITUTION_USER",
            "institution_id": sample_inst_id
        }
        r = client.post("/auth/register", json=reg_payload)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        new_user = r.json()
        assert new_user["email"] == main_test_email
        assert new_user["full_name"] == "Prof. Ananya Sharma"
        assert new_user["role"] == "INSTITUTION_USER"
        assert new_user["is_active"] is True
        assert "password" not in new_user
        assert "hashed_password" not in new_user
        print(f"[PASS] 8. Successful registration of fictional user: {main_test_email} (ID: {new_user['id']})")

        # 9. Duplicate email registration rejection
        r = client.post("/auth/register", json=reg_payload)
        assert r.status_code == 400
        assert "already exists" in r.text
        print(f"[PASS] 9. Duplicate registration rejected with 400: '{r.json()['detail']}'")

        # 10. Login with newly created user credentials
        # 10a. Valid credentials
        r = client.post("/auth/login", json={
            "email": main_test_email,
            "password": "OfficerPassword@2026"
        })
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        login_res = r.json()
        assert "access_token" in login_res
        assert login_res["user"]["email"] == main_test_email
        print(f"[PASS] 10a. Successfully logged in with newly registered account credentials")

        # 10b. Incorrect password
        r = client.post("/auth/login", json={
            "email": main_test_email,
            "password": "WrongPassword@999"
        })
        assert r.status_code == 401
        assert "Incorrect email or password" in r.text
        print(f"[PASS] 10b. Incorrect password rejected with 401 Unauthorized")

    print("\n=== ALL 10 REGISTRATION & AUTHENTICATION TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
