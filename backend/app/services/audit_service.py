import json
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.models.user import User

def log_audit_event(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    actor: Optional[User] = None,
    actor_email: Optional[str] = None,
    actor_role: Optional[str] = None,
    details: Optional[str] = None,
    before_state: Optional[Any] = None,
    after_state: Optional[Any] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """Safely record an immutable audit event."""
    # Convert states to JSON string if dict or model
    before_json = None
    after_json = None
    
    if before_state is not None:
        before_json = json.dumps(before_state, default=str) if isinstance(before_state, (dict, list)) else str(before_state)
    if after_state is not None:
        after_json = json.dumps(after_state, default=str) if isinstance(after_state, (dict, list)) else str(after_state)
        
    audit_entry = AuditLog(
        actor_id=actor.id if actor else None,
        actor_email=actor.email if actor else actor_email,
        actor_role=actor.role.value if actor else actor_role,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        before_state=before_json,
        after_state=after_json,
        ip_address=ip_address
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    return audit_entry
