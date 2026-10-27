from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from app.models.enums import UserRole

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    requires_mfa: bool = False
    temp_mfa_token: Optional[str] = None
    user: Optional[dict] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8)
    role: UserRole = UserRole.INSTITUTION_USER
    institution_id: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)

# MFA Schemas
class MFASetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    qr_code_base64: str
    manual_setup_key: str

class MFAVerifyEnrollmentRequest(BaseModel):
    secret: str
    code: str

class MFAEnrollmentSuccessResponse(BaseModel):
    message: str
    backup_recovery_codes: List[str]

class MFALoginChallengeRequest(BaseModel):
    temp_mfa_token: str
    code: Optional[str] = None
    recovery_code: Optional[str] = None
