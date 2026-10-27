import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    actor_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_email = Column(String(255), nullable=True)
    actor_role = Column(String(50), nullable=True)
    
    action = Column(String(100), nullable=False, index=True)  # LOGIN, FDR_CREATE, FDR_STATUS_UPDATE, etc.
    entity_type = Column(String(50), nullable=False, index=True)  # FDR, USER, DOCUMENT, etc.
    entity_id = Column(String(100), nullable=True, index=True)
    
    details = Column(Text, nullable=True)
    before_state = Column(Text, nullable=True)
    after_state = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False, index=True)

    actor = relationship("User", back_populates="audit_logs")
