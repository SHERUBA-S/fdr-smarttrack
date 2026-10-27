import enum

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    INSTITUTION_USER = "INSTITUTION_USER"
    REVIEWING_OFFICIAL = "REVIEWING_OFFICIAL"
    READONLY_AUDITOR = "READONLY_AUDITOR"

class FDRStatus(str, enum.Enum):
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    ADDITIONAL_INFO_REQUIRED = "Additional Information Required"
    VERIFIED_AUTHORIZED = "Verified by Authorized Source"
    MANUALLY_REVIEWED = "Manually Reviewed"
    VERIFICATION_PENDING = "Verification Pending"
    APPROVED = "Approved"
    RENEWAL_PENDING = "Renewal Pending"
    RELEASE_REQUESTED = "Release Requested"
    RELEASED = "Released"
    REJECTED = "Rejected"
    EXPIRED = "Expired"

class VerificationOutcome(str, enum.Enum):
    PASSED = "Passed"
    WARNING = "Warning"
    FAILED = "Failed"
    NOT_CHECKED = "Not Checked"
    AWAITING_EXTERNAL = "Awaiting External Verification"

class SeverityLevel(str, enum.Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MORE_INFO_REQUESTED = "MORE_INFO_REQUESTED"

class DocumentType(str, enum.Enum):
    FDR_RECEIPT = "FDR_RECEIPT"
    RENEWAL_LETTER = "RENEWAL_LETTER"
    RELEASE_APPROVAL = "RELEASE_APPROVAL"
    BANK_CONFIRMATION = "BANK_CONFIRMATION"
    OTHER = "OTHER"
