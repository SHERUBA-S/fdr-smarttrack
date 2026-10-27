import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.enums import UserRole
from app.models.institution import Institution
from app.core.security import hash_password
from app.services.synthetic_data_service import generate_synthetic_dataset

def seed():
    print("Creating all tables in PostgreSQL if not present...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("Checking default demo users...")
        users_data = [
            {
                "email": "admin@smarttrack.gov.in",
                "full_name": "Super Administrator",
                "password": "AdminPassword@123",
                "role": UserRole.SUPER_ADMIN
            },
            {
                "email": "reviewer@smarttrack.gov.in",
                "full_name": "Reviewing Official (Finance Wing)",
                "password": "ReviewerPassword@123",
                "role": UserRole.REVIEWING_OFFICIAL
            },
            {
                "email": "auditor@smarttrack.gov.in",
                "full_name": "Senior Statutory Auditor",
                "password": "AuditorPassword@123",
                "role": UserRole.READONLY_AUDITOR
            }
        ]

        for u in users_data:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                new_user = User(
                    email=u["email"],
                    full_name=u["full_name"],
                    hashed_password=hash_password(u["password"]),
                    role=u["role"],
                    is_active=True,
                    is_mfa_enabled=False
                )
                db.add(new_user)
                print(f"Created demo user: {u['email']} [{u['role'].value}]")
            else:
                print(f"User already exists: {u['email']}")

        db.commit()

        # Check if institutions exist; if not, generate demo dataset
        inst_count = db.query(Institution).count()
        if inst_count == 0:
            print("No institutions found. Generating baseline demo dataset...")
            res = generate_synthetic_dataset(db, mode="DEMO", seed=42)
            print(f"Demo dataset generated successfully: {res}")
        else:
            print(f"Found {inst_count} existing institutions in database.")

        print("\nAll demo accounts and datasets ready!")
        print("----------------------------------------------------------------")
        print("Demo Accounts:")
        print("1. Super Admin: admin@smarttrack.gov.in / AdminPassword@123")
        print("2. Reviewer:    reviewer@smarttrack.gov.in / ReviewerPassword@123")
        print("3. Institution: institution@smarttrack.gov.in / DemoPassword@123")
        print("4. Auditor:     auditor@smarttrack.gov.in / AuditorPassword@123")
        print("----------------------------------------------------------------\n")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
