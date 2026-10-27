from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.institution import Bank
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.institution import BankCreate, BankResponse

router = APIRouter()

@router.get("/", response_model=List[BankResponse])
def list_banks(
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List supported banks with branch and IFSC prefixes."""
    query = db.query(Bank).filter(Bank.is_active == True)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(Bank.name.ilike(s) | Bank.code.ilike(s))
    return query.order_by(Bank.name).all()

@router.post("/", response_model=BankResponse)
def create_bank(
    data: BankCreate,
    current_user: User = Depends(require_roles([UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    """Add a new supported banking entity (Super Admin only)."""
    bank = Bank(
        code=data.code.strip().upper(),
        name=data.name.strip(),
        branch=data.branch,
        ifsc_prefix=data.ifsc_prefix,
        is_active=data.is_active,
        is_synthetic=False
    )
    db.add(bank)
    db.commit()
    db.refresh(bank)
    return bank
