import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(50), default="MATURITY_ALERT", nullable=False, index=True)  # MATURITY_ALERT, REVIEW_UPDATE, SYSTEM
    link = Column(String(255), nullable=True)
    
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    fdr_id = Column(String(36), nullable=True, index=True)
    event_key = Column(String(255), nullable=True, index=True)  # Deduplication key, e.g. "fdr-123-maturity-30"
    
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False, index=True)

    user = relationship("User", back_populates="notifications")
