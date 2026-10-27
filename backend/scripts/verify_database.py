import os
import sys
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.database import SessionLocal, check_db_health
from app.models.institution import Bank, Institution
from app.models.fdr import FDRRecord
from sqlalchemy import create_engine, text

def run_db_verification():
    print("=== TASK 1: DATABASE VERIFICATION ===")
    
    # 1. Connection check
    health = check_db_health()
    print(f"1. Database Health Check: {'PASSED (Connected)' if health else 'FAILED'}")
    assert health is True, "Database health check failed!"

    # 2. Inspect existing records
    db = SessionLocal()
    bank_cnt = db.query(Bank).count()
    inst_cnt = db.query(Institution).count()
    fdr_cnt = db.query(FDRRecord).count()
    print(f"2. Existing Operational Counts in main DB (fdr_smarttrack_db):")
    print(f"   - Banks: {bank_cnt}")
    print(f"   - Institutions: {inst_cnt}")
    print(f"   - FDR Records: {fdr_cnt}")

    # 3. Test Write to Main DB
    test_code = f"VERIFY_{uuid.uuid4().hex[:6].upper()}"
    test_bank = Bank(
        code=test_code,
        name="Verification Test Bank Ltd",
        branch="Compliance Audit Branch",
        ifsc_prefix="TEST0099",
        is_active=True,
        is_synthetic=True
    )
    db.add(test_bank)
    db.commit()
    db.refresh(test_bank)
    saved_id = test_bank.id
    print(f"3. Test Write: Successfully inserted record with ID: {saved_id} (code: {test_code})")

    # 4. Test Read from Main DB
    fetched = db.query(Bank).filter(Bank.id == saved_id).first()
    assert fetched is not None, "Test record was not found after commit!"
    assert fetched.code == test_code, "Test record data corrupted!"
    print(f"4. Test Read: Successfully fetched inserted record back from fdr_smarttrack_db.")

    # 5. Clean up test record from Main DB
    db.delete(fetched)
    db.commit()
    print("5. Test Record Cleanup: Cleaned up test record safely from main DB.")
    db.close()

    # 6. Verify Test Database Separation
    print(f"6. Checking Test Database Separation:")
    print(f"   - Main DB URL: {settings.DATABASE_URL}")
    print(f"   - Test DB URL: {settings.TEST_DATABASE_URL}")
    test_engine = create_engine(settings.TEST_DATABASE_URL)
    with test_engine.connect() as test_conn:
        test_db_name = test_conn.execute(text("SELECT current_database();")).scalar()
        print(f"   - Connected to Test DB: {test_db_name}")
        assert test_db_name == "fdr_smarttrack_test_db", "Test DB is not separate!"
        
        # Verify test DB table separation
        check_table_sql = text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'banks');")
        has_table = test_conn.execute(check_table_sql).scalar()
        if has_table:
            cnt = test_conn.execute(text("SELECT count(*) FROM banks WHERE code = :c"), {"c": test_code}).scalar()
            assert cnt == 0, "Record was found in test DB; separation violated!"
        print("   - Isolation verified: fdr_smarttrack_test_db is completely separate.")

    print("\n=== ALL DATABASE VERIFICATION CHECKS PASSED ===")

if __name__ == "__main__":
    run_db_verification()
