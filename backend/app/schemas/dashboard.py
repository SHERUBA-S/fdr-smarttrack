from datetime import date
from decimal import Decimal
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class StatusCount(BaseModel):
    status: str
    count: int

class MaturityMonthCount(BaseModel):
    month_year: str
    count: int
    total_amount: Decimal

class BankDistribution(BaseModel):
    bank_name: str
    count: int
    total_amount: Decimal

class UrgentActionItem(BaseModel):
    fdr_id: str
    fdr_number: str
    institution_name: str
    bank_name: str
    principal_amount: Decimal
    maturity_date: date
    days_to_maturity: int
    status: str
    urgency: str  # OVERDUE, CRITICAL (<=7d), WARNING (<=30d), UPCOMING (<=90d)
    action_type: str  # RENEWAL_DUE, REVIEW_PENDING, RELEASE_PENDING, DISCREPANCY_FLAG

class DashboardMetricsResponse(BaseModel):
    total_institutions: int
    total_fdrs: int
    total_recorded_principal: Decimal  # Note: Administrative record total, not portal custody/balance
    records_awaiting_review: int
    records_with_discrepancies: int
    fdrs_approaching_maturity_30d: int
    fdrs_overdue_maturity: int
    pending_renewal_requests: int
    pending_release_requests: int
    documents_requiring_verification: int
    
    status_distribution: List[StatusCount]
    maturity_timeline: List[MaturityMonthCount]
    bank_distribution: List[BankDistribution]
    urgent_actions: List[UrgentActionItem]
    
    disclaimer: str = "Total principal amount represents recorded administrative figures from institution receipts. FDR SmartTrack does not hold or custody financial deposits."
