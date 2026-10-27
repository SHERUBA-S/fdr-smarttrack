import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, Numeric, Float,
    ForeignKey, Enum as SAEnum, Text, Integer, Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import FDRStatus, VerificationOutcome, SeverityLevel, DocumentType

def get_utc_now():
    return datetime.now(timezone.utc)

class FDRRecord(Base):
    __tablename__ = "fdr_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    fdr_number = Column(String(100), index=True, nullable=False)
    
    institution_id = Column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_id = Column(String(36), ForeignKey("banks.id", ondelete="SET NULL"), nullable=True, index=True)
    
    bank_name = Column(String(255), nullable=False)
    branch_name = Column(String(255), nullable=True)
    
    # Financial precision: Decimal(15, 2)
    principal_amount = Column(Numeric(precision=15, scale=2), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    interest_rate = Column(Numeric(precision=5, scale=2), nullable=True)
    
    issue_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=False, index=True)
    
    purpose = Column(String(255), default="Institutional Security Deposit", nullable=False)
    status = Column(SAEnum(FDRStatus), default=FDRStatus.DRAFT, nullable=False, index=True)
    verification_status = Column(SAEnum(VerificationOutcome), default=VerificationOutcome.NOT_CHECKED, nullable=False)
    
    assigned_reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    has_discrepancy = Column(Boolean, default=False, nullable=False, index=True)
    discrepancy_notes = Column(Text, nullable=True)
    anomaly_score = Column(Float, nullable=True)  # Experimental ML review signal
    is_synthetic = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships
    institution = relationship("Institution", back_populates="fdr_records")
    bank = relationship("Bank", back_populates="fdr_records")
    assigned_reviewer = relationship("User", foreign_keys=[assigned_reviewer_id])
    documents = relationship("FDRDocument", back_populates="fdr", cascade="all, delete-orphan")
    verification_checks = relationship("VerificationCheck", back_populates="fdr", cascade="all, delete-orphan")
    renewal_requests = relationship("RenewalRequest", back_populates="fdr", cascade="all, delete-orphan")
    release_requests = relationship("ReleaseRequest", back_populates="fdr", cascade="all, delete-orphan")
    review_decisions = relationship("ReviewDecision", back_populates="fdr", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_fdr_inst_bank_num", "institution_id", "bank_name", "fdr_number"),
    )

class FDRDocument(Base):
    __tablename__ = "fdr_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    fdr_id = Column(String(36), ForeignKey("fdr_records.id", ondelete="CASCADE"), nullable=False, index=True)
    
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256
    document_type = Column(SAEnum(DocumentType), default=DocumentType.FDR_RECEIPT, nullable=False)
    
    ocr_status = Column(String(50), default="PENDING", nullable=False)  # PENDING, COMPLETED, FAILED
    raw_ocr_text = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    fdr = relationship("FDRRecord", back_populates="documents")
    extracted_fields = relationship("ExtractedDocumentField", back_populates="document", cascade="all, delete-orphan")

class ExtractedDocumentField(Base):
    __tablename__ = "extracted_document_fields"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("fdr_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    field_name = Column(String(100), nullable=False, index=True)
    extracted_value = Column(String(500), nullable=True)
    confidence = Column(Float, default=0.0, nullable=False)
    page_number = Column(Integer, default=1, nullable=False)
    user_corrected_value = Column(String(500), nullable=True)
    is_corrected = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    document = relationship("FDRDocument", back_populates="extracted_fields")

class VerificationCheck(Base):
    __tablename__ = "verification_checks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fdr_id = Column(String(36), ForeignKey("fdr_records.id", ondelete="CASCADE"), nullable=False, index=True)
    
    check_name = Column(String(100), nullable=False, index=True)
    outcome = Column(SAEnum(VerificationOutcome), nullable=False)
    severity = Column(SAEnum(SeverityLevel), default=SeverityLevel.INFO, nullable=False)
    evidence = Column(Text, nullable=True)
    explanation = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=True)
    requires_human_review = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    fdr = relationship("FDRRecord", back_populates="verification_checks")
