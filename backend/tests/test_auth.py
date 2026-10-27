import pyotp
from app.core.security import verify_password, hash_password
from app.models.enums import UserRole

def test_health_check(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"]["status"] == "connected"

def test_password_hashing():
    pw = "SecretPassphrase#2026"
    h = hash_password(pw)
    assert h != pw
    assert verify_password(pw, h) is True
    assert verify_password("WrongPassword", h) is False

def test_login_success(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@smarttrack.gov.in",
        "password": "AdminPassword@123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "SUPER_ADMIN"

def test_login_failure_invalid_credentials(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@smarttrack.gov.in",
        "password": "IncorrectPassword"
    })
    assert res.status_code == 401
    assert "access_token" not in res.json()

def test_totp_mfa_workflow(client):
    # Register a dedicated user for MFA testing to isolate from main admin user
    test_email = "mfa_tester@smarttrack.gov.in"
    test_pass = "MfaTestPassword@123"
    
    # Register if not exists
    reg_res = client.post("/api/v1/auth/register", json={
        "email": test_email,
        "full_name": "MFA Test Account",
        "password": test_pass,
        "role": "SUPER_ADMIN"
    })
    
    # Login to obtain user token
    login_res = client.post("/api/v1/auth/login", json={
        "email": test_email,
        "password": test_pass
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Setup MFA
    res_setup = client.post("/api/v1/auth/mfa/setup", headers=headers)
    assert res_setup.status_code == 200
    setup_data = res_setup.json()
    assert "secret" in setup_data
    assert "qr_code_base64" in setup_data
    secret = setup_data["secret"]

    # 2. Verify enrollment with real TOTP code
    totp = pyotp.TOTP(secret)
    current_code = totp.now()

    res_verify = client.post("/api/v1/auth/mfa/verify-enrollment", headers=headers, json={
        "secret": secret,
        "code": current_code
    })
    assert res_verify.status_code == 200
    verify_data = res_verify.json()
    assert len(verify_data["backup_recovery_codes"]) == 8
    first_recovery_code = verify_data["backup_recovery_codes"][0]

    # 3. Next login will require MFA challenge
    res_login_mfa = client.post("/api/v1/auth/login", json={
        "email": test_email,
        "password": test_pass
    })
    assert res_login_mfa.status_code == 200
    login_mfa_data = res_login_mfa.json()
    assert login_mfa_data["requires_mfa"] is True
    temp_token = login_mfa_data["temp_mfa_token"]

    # 4. Complete challenge using recovery code
    res_challenge = client.post("/api/v1/auth/mfa/challenge", json={
        "temp_mfa_token": temp_token,
        "recovery_code": first_recovery_code
    })
    assert res_challenge.status_code == 200
    challenge_data = res_challenge.json()
    assert "access_token" in challenge_data
    assert challenge_data["requires_mfa"] is False
