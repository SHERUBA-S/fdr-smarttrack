from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import RequestStatus, FDRStatus

class RenewalRequestCreate(BaseModel):
    new_maturity_date: date
    rationale: str = Field(min_length=10)
    supporting_doc_name: Optional[str] = None

class RenewalResponse(BaseModel):
    id: str
    fdr_id: str
    requested_by_id: Optional[str] = None
    new_maturity_date: date
    status: RequestStatus
    rationale: str
    supporting_doc_name: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ReleaseRequestCreate(BaseModel):
    clearance_reference: str = Field(min_length=3)
    rationale: str = Field(min_length=10)
    supporting_doc_name: Optional[str] = None

class ReleaseResponse(BaseModel):
    id: str
    fdr_id: str
    requested_by_id: Optional[str] = None
    clearance_reference: str
    status: RequestStatus
    rationale: str
    supporting_doc_name: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ReviewDecisionCreate(BaseModel):
    decision_type: str = Field(pattern="^(APPROVE|REJECT|REQUEST_INFO|RENEW|RELEASE)$")
    new_status: FDRStatus
    reason: str = Field(min_length=5)
    remarks: Optional[str] = None

class ReviewDecisionResponse(BaseModel):
    id: str
    fdr_id: str
    reviewer_id: Optional[str] = None
    previous_status: FDRStatus
    new_status: FDRStatus
    decision_type: str
    reason: str
    remarks: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
