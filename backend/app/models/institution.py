import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), index=True, nullable=False)
    state = Column(String(100), index=True, nullable=False)
    city = Column(String(100), nullable=False)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships
    members = relationship("User", back_populates="institution")
    memberships = relationship("InstitutionMembership", back_populates="institution", cascade="all, delete-orphan")
    fdr_records = relationship("FDRRecord", back_populates="institution", cascade="all, delete-orphan")

class InstitutionMembership(Base):
    __tablename__ = "institution_memberships"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_id = Column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    role_title = Column(String(100), default="Authorized Signatory")
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    institution = relationship("Institution", back_populates="memberships")

class Bank(Base):
    __tablename__ = "banks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), index=True, nullable=False)
    branch = Column(String(255), nullable=True)
    ifsc_prefix = Column(String(20), index=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    fdr_records = relationship("FDRRecord", back_populates="bank")
