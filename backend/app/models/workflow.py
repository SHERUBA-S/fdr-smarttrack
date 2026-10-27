import uuid
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import RequestStatus, FDRStatus

def get_utc_now():
    return datetime.now(timezone.utc)

class RenewalRequest(Base):
    __tablename__ = "renewal_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    fdr_id = Column(String(36), ForeignKey("fdr_records.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    new_maturity_date = Column(Date, nullable=False)
    status = Column(SAEnum(RequestStatus), default=RequestStatus.PENDING, nullable=False, index=True)
    rationale = Column(Text, nullable=False)
    supporting_doc_name = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    fdr = relationship("FDRRecord", back_populates="renewal_requests")
    requested_by = relationship("User", foreign_keys=[requested_by_id])

class ReleaseRequest(Base):
    __tablename__ = "release_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    fdr_id = Column(String(36), ForeignKey("fdr_records.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    clearance_reference = Column(String(100), nullable=False)
    status = Column(SAEnum(RequestStatus), default=RequestStatus.PENDING, nullable=False, index=True)
    rationale = Column(Text, nullable=False)
    supporting_doc_name = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    fdr = relationship("FDRRecord", back_populates="release_requests")
    requested_by = relationship("User", foreign_keys=[requested_by_id])

class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fdr_id = Column(String(36), ForeignKey("fdr_records.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    previous_status = Column(SAEnum(FDRStatus), nullable=False)
    new_status = Column(SAEnum(FDRStatus), nullable=False)
    decision_type = Column(String(50), nullable=False)  # APPROVE, REJECT, REQUEST_INFO, RENEW, RELEASE
    reason = Column(Text, nullable=False)
    remarks = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    fdr = relationship("FDRRecord", back_populates="review_decisions")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
