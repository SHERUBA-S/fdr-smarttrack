from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.institution import Institution
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.institution import InstitutionCreate, InstitutionUpdate, InstitutionResponse
from app.services.audit_service import log_audit_event

router = APIRouter()

@router.get("/", response_model=List[InstitutionResponse])
def list_institutions(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List institutions with search and pagination."""
    query = db.query(Institution)
    
    # Institution users only see their own institution
    if current_user.role == UserRole.INSTITUTION_USER:
        if not current_user.institution_id:
            return []
        query = query.filter(Institution.id == current_user.institution_id)
    elif search:
        s = f"%{search.strip()}%"
        query = query.filter(Institution.name.ilike(s) | Institution.code.ilike(s) | Institution.city.ilike(s))
        
    return query.offset(skip).limit(limit).all()

@router.get("/public", response_model=List[InstitutionResponse])
def list_public_institutions(db: Session = Depends(get_db)):
    """Public active institutions list for registration dropdown."""
    return db.query(Institution).filter(Institution.is_active == True).order_by(Institution.name).all()

@router.get("/{institution_id}", response_model=InstitutionResponse)
def get_institution(
    institution_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve details for a single institution."""
    if current_user.role == UserRole.INSTITUTION_USER and current_user.institution_id != institution_id:
        raise HTTPException(status_code=403, detail="Access denied")

    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    return inst

@router.post("/", response_model=InstitutionResponse)
def create_institution(
    data: InstitutionCreate,
    current_user: User = Depends(require_roles([UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    """Register a new institution (Super Admin only)."""
    existing = db.query(Institution).filter(Institution.code == data.code.strip().upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Institution code already exists")

    inst = Institution(
        code=data.code.strip().upper(),
        name=data.name.strip(),
        state=data.state.strip(),
        city=data.city.strip(),
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        is_active=data.is_active,
        is_synthetic=False
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)

    log_audit_event(
        db=db,
        action="INSTITUTION_CREATED",
        entity_type="INSTITUTION",
        entity_id=inst.id,
        actor=current_user,
        details=f"Created {inst.name} ({inst.code})"
    )

    return inst
