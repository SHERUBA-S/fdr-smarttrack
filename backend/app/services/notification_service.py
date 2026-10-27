import logging
import smtplib
from email.mime.text import MIMEText
from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.notification import Notification
from app.models.fdr import FDRRecord
from app.models.user import User
from app.models.enums import UserRole, FDRStatus

logger = logging.getLogger(__name__)

def create_notification(
    db: Session,
    user_id: str,
    title: str,
    message: str,
    category: str = "SYSTEM",
    link: Optional[str] = None,
    fdr_id: Optional[str] = None,
    event_key: Optional[str] = None
) -> Optional[Notification]:
    """Create in-app notification with deduplication check."""
    if event_key:
        existing = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.event_key == event_key
        ).first()
        if existing:
            return existing  # Skip duplicate notification
            
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        category=category,
        link=link,
        fdr_id=fdr_id,
        event_key=event_key
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif

def send_email_notification(to_email: str, subject: str, content: str) -> bool:
    """Send email via SMTP if configured, otherwise log safely in development mode."""
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.info(f"[DEV EMAIL ADAPTER] To: {to_email} | Subject: {subject} | Body: {content}")
        return True
        
    try:
        msg = MIMEText(content, "plain")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_email

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False

def check_fdr_maturity_alerts(db: Session) -> int:
    """
    Scheduled job: Check FDR records approaching maturity or overdue.
    Creates deduplicated alerts for institution users and reviewing officials.
    """
    today = date.today()
    created_count = 0
    
    # Active statuses that need maturity monitoring
    monitored_statuses = [
        FDRStatus.APPROVED,
        FDRStatus.VERIFIED_AUTHORIZED,
        FDRStatus.MANUALLY_REVIEWED,
        FDRStatus.SUBMITTED
    ]
    
    active_fdrs = db.query(FDRRecord).filter(FDRRecord.status.in_(monitored_statuses)).all()
    
    for fdr in active_fdrs:
        days_remaining = (fdr.maturity_date - today).days
        
        # Determine institution users to notify
        inst_users = db.query(User).filter(
            User.institution_id == fdr.institution_id,
            User.role == UserRole.INSTITUTION_USER,
            User.is_active == True
        ).all()
        
        # Check window alerts (e.g. 90, 60, 30, 7, 1 days)
        for window in settings.ALERT_WINDOWS_DAYS:
            # Trigger alert when days_remaining is within [window - 1, window]
            if 0 <= days_remaining <= window and (window == 1 or days_remaining > window - 7):
                event_key = f"fdr_{fdr.id}_maturity_{window}d"
                title = f"FDR Maturity Alert: {window} Days Remaining"
                msg = f"FDR #{fdr.fdr_number} for {fdr.bank_name} (Principal: ₹{fdr.principal_amount:,.2f}) will mature on {fdr.maturity_date}. Please review renewal or release requirements."
                
                for u in inst_users:
                    res = create_notification(
                        db=db,
                        user_id=u.id,
                        title=title,
                        message=msg,
                        category="MATURITY_ALERT",
                        link=f"/fdrs/{fdr.id}",
                        fdr_id=fdr.id,
                        event_key=f"{event_key}_{u.id}"
                    )
                    if res:
                        created_count += 1
                        
        # Check overdue follow-up
        if days_remaining < 0:
            overdue_days = abs(days_remaining)
            event_key = f"fdr_{fdr.id}_overdue_{overdue_days // 15}"  # alert every 15 days of overdue
            title = f"OVERDUE: FDR #{fdr.fdr_number} Matured {overdue_days} Days Ago"
            msg = f"FDR #{fdr.fdr_number} reached maturity on {fdr.maturity_date}. Urgent administrative follow-up required for renewal or release."
            
            for u in inst_users:
                res = create_notification(
                    db=db,
                    user_id=u.id,
                    title=title,
                    message=msg,
                    category="OVERDUE_ALERT",
                    link=f"/fdrs/{fdr.id}",
                    fdr_id=fdr.id,
                    event_key=f"{event_key}_{u.id}"
                )
                if res:
                    created_count += 1
                    
    return created_count
