from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_roles
from app.models.enums import UserRole
from app.models.fdr import FDRRecord, FDRDocument, VerificationCheck
from app.models.institution import Institution, Bank
from app.models.workflow import RenewalRequest, ReleaseRequest
from app.services.synthetic_data_service import generate_synthetic_dataset
from app.services.audit_service import log_audit_event

router = APIRouter()

class GenerateDatasetRequest(BaseModel):
    mode: str = "DEMO"  # DEMO or FULL
    seed: int = 42

@router.post("/generate")
def trigger_dataset_generation(
    data: GenerateDatasetRequest,
    current_user = Depends(require_roles([UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    """Generate synthetic institutions, banks, FDR records, and workflows for testing."""
    result = generate_synthetic_dataset(db=db, mode=data.mode, seed=data.seed)
    
    log_audit_event(
        db=db,
        action="SYNTHETIC_DATASET_GENERATED",
        entity_type="SYSTEM",
        actor=current_user,
        details=f"Generated {data.mode} dataset ({result.get('fdrs_created')} FDRs)"
    )

    return result

@router.post("/reset-demo-data")
def reset_demo_data(
    current_user = Depends(require_roles([UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    """Reset and remove synthetic demo data safely."""
    # Delete synthetic FDRs and cascade
    deleted_fdrs = db.query(FDRRecord).filter(FDRRecord.is_synthetic == True).delete(synchronize_session=False)
    deleted_insts = db.query(Institution).filter(Institution.is_synthetic == True).delete(synchronize_session=False)
    deleted_banks = db.query(Bank).filter(Bank.is_synthetic == True).delete(synchronize_session=False)
    db.commit()

    log_audit_event(
        db=db,
        action="DEMO_DATA_RESET",
        entity_type="SYSTEM",
        actor=current_user,
        details=f"Purged synthetic records: {deleted_fdrs} FDRs, {deleted_insts} institutions"
    )

    return {
        "status": "SUCCESS",
        "deleted_fdrs": deleted_fdrs,
        "deleted_institutions": deleted_insts,
        "deleted_banks": deleted_banks
    }
