from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    category: str
    link: Optional[str] = None
    is_read: bool
    fdr_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    unread_count: int
