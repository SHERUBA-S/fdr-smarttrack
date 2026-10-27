from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, model_validator
from app.models.enums import FDRStatus, VerificationOutcome, SeverityLevel, DocumentType

class ExtractedFieldResponse(BaseModel):
    id: str
    field_name: str
    extracted_value: Optional[str] = None
    confidence: float
    page_number: int
    user_corrected_value: Optional[str] = None
    is_corrected: bool

    model_config = ConfigDict(from_attributes=True)

class ExtractedFieldCorrectionRequest(BaseModel):
    user_corrected_value: str

class FDRDocumentResponse(BaseModel):
    id: str
    file_name: str
    file_size_bytes: int
    mime_type: str
    document_type: DocumentType
    ocr_status: str
    created_at: datetime
    extracted_fields: List[ExtractedFieldResponse] = []

    model_config = ConfigDict(from_attributes=True)

class VerificationCheckResponse(BaseModel):
    id: str
    check_name: str
    outcome: VerificationOutcome
    severity: SeverityLevel
    evidence: Optional[str] = None
    explanation: str
    recommended_action: Optional[str] = None
    requires_human_review: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FDRCreate(BaseModel):
    fdr_number: str = Field(min_length=2, max_length=100)
    institution_id: str
    bank_id: Optional[str] = None
    bank_name: str = Field(min_length=2, max_length=255)
    branch_name: Optional[str] = None
    principal_amount: Decimal = Field(gt=0, decimal_places=2)
    currency: str = "INR"
    interest_rate: Optional[Decimal] = Field(default=None, ge=0, le=100, decimal_places=2)
    issue_date: date
    maturity_date: date
    purpose: str = "Institutional Security Deposit"

    @model_validator(mode="after")
    def validate_dates(self):
        if self.maturity_date <= self.issue_date:
            raise ValueError("Maturity date must be after issue date")
        return self

class FDRUpdate(BaseModel):
    fdr_number: Optional[str] = None
    bank_name: Optional[str] = None
    branch_name: Optional[str] = None
    principal_amount: Optional[Decimal] = None
    interest_rate: Optional[Decimal] = None
    issue_date: Optional[date] = None
    maturity_date: Optional[date] = None
    purpose: Optional[str] = None
    status: Optional[FDRStatus] = None

class FDRResponse(BaseModel):
    id: str
    fdr_number: str
    institution_id: str
    institution_name: Optional[str] = None
    bank_id: Optional[str] = None
    bank_name: str
    branch_name: Optional[str] = None
    principal_amount: Decimal
    currency: str
    interest_rate: Optional[Decimal] = None
    issue_date: date
    maturity_date: date
    purpose: str
    status: FDRStatus
    verification_status: VerificationOutcome
    assigned_reviewer_id: Optional[str] = None
    has_discrepancy: bool
    discrepancy_notes: Optional[str] = None
    anomaly_score: Optional[float] = None
    is_synthetic: bool
    created_at: datetime
    updated_at: datetime
    
    documents: List[FDRDocumentResponse] = []
    verification_checks: List[VerificationCheckResponse] = []

    model_config = ConfigDict(from_attributes=True)

class FDRListResponse(BaseModel):
    items: List[FDRResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
