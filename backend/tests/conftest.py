import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.enums import UserRole
from app.models.institution import Institution
from app.core.security import hash_password

@pytest.fixture(scope="session")
def client():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="session")
def admin_token(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@smarttrack.gov.in",
        "password": "AdminPassword@123"
    })
    return res.json()["access_token"]

@pytest.fixture(scope="session")
def reviewer_token(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "reviewer@smarttrack.gov.in",
        "password": "ReviewerPassword@123"
    })
    return res.json()["access_token"]

@pytest.fixture(scope="session")
def institution_token(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "institution@smarttrack.gov.in",
        "password": "DemoPassword@123"
    })
    return res.json()["access_token"]
