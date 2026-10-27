from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_roles
from app.core.security import hash_password
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.audit_service import log_audit_event

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user = Depends(require_roles([UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    """List system users (Super Admin only)."""
    return db.query(User).offset(skip).limit(limit).all()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    current_user = Depends(require_roles([UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    """Create a new user with assigned role (Super Admin only)."""
    existing = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email.lower().strip(),
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role=data.role,
        institution_id=data.institution_id,
        is_active=data.is_active,
        is_mfa_enabled=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_audit_event(
        db=db,
        action="ADMIN_CREATED_USER",
        entity_type="USER",
        entity_id=user.id,
        actor=current_user,
        details=f"Created {user.email} with role {user.role.value}"
    )

    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    data: UserUpdate,
    current_user = Depends(require_roles([UserRole.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    """Update user details or role (Super Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.full_name is not None: user.full_name = data.full_name
    if data.role is not None: user.role = data.role
    if data.is_active is not None: user.is_active = data.is_active
    if data.institution_id is not None: user.institution_id = data.institution_id
    if data.password: user.hashed_password = hash_password(data.password)

    db.commit()
    db.refresh(user)

    log_audit_event(
        db=db,
        action="ADMIN_UPDATED_USER",
        entity_type="USER",
        entity_id=user.id,
        actor=current_user,
        details=f"Updated user {user.email}"
    )

    return user
