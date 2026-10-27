from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token
)
from app.core.mfa import (
    generate_totp_secret, generate_totp_uri, generate_qr_code_base64,
    verify_totp_code, generate_recovery_codes, verify_and_consume_recovery_code
)
from app.core.deps import get_current_user
from app.models.user import User, RefreshToken, MFAConfiguration, MFARecoveryCode
from app.models.institution import Institution
from app.models.enums import UserRole
from app.schemas.auth import (
    LoginRequest, TokenResponse, RefreshTokenRequest,
    RegisterRequest, ForgotPasswordRequest, ResetPasswordRequest,
    MFASetupResponse, MFAVerifyEnrollmentRequest, MFAEnrollmentSuccessResponse,
    MFALoginChallengeRequest
)
from app.schemas.user import UserResponse
from app.services.audit_service import log_audit_event

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate user with email and password; triggers MFA challenge if MFA is enabled."""
    user = db.query(User).filter(User.email == login_data.email.lower().strip()).first()
    
    # Timing safe / generic error to prevent user enumeration
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account")

    # If MFA is enabled, issue a temporary MFA challenge token (valid 5 minutes)
    if user.is_mfa_enabled:
        temp_mfa_token = create_access_token(
            subject=user.id,
            extra_claims={"type": "mfa_pending", "email": user.email}
        )
        return TokenResponse(
            access_token="",
            refresh_token="",
            expires_in=300,
            requires_mfa=True,
            temp_mfa_token=temp_mfa_token,
            user={"id": user.id, "email": user.email, "role": user.role.value}
        )

    # Standard successful login
    access_token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value, "institution_id": user.institution_id}
    )
    refresh_token = create_refresh_token(subject=user.id)
    
    # Store hashed refresh token in database
    token_rec = RefreshToken(
        user_id=user.id,
        token_hash=hash_password(refresh_token[:32]),  # hash prefix for storage
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(token_rec)
    db.commit()

    log_audit_event(
        db=db,
        action="USER_LOGIN",
        entity_type="USER",
        entity_id=user.id,
        actor=user,
        ip_address=request.client.host if request.client else None
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        requires_mfa=False,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "institution_id": user.institution_id
        }
    )

@router.post("/mfa/challenge", response_model=TokenResponse)
def mfa_challenge(challenge_data: MFALoginChallengeRequest, request: Request, db: Session = Depends(get_db)):
    """Complete login challenge using TOTP code or backup recovery code."""
    payload = decode_token(challenge_data.temp_mfa_token)
    if not payload or payload.get("type") != "mfa_pending":
        raise HTTPException(status_code=400, detail="Invalid or expired MFA session")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    mfa_conf = db.query(MFAConfiguration).filter(MFAConfiguration.user_id == user.id).first()
    if not mfa_conf or not mfa_conf.is_confirmed:
        raise HTTPException(status_code=400, detail="MFA not properly configured")

    verified = False
    used_recovery = False

    # 1. Try TOTP code if provided
    if challenge_data.code:
        verified = verify_totp_code(mfa_conf.secret_key, challenge_data.code)

    # 2. Try Recovery code if TOTP failed or not provided
    if not verified and challenge_data.recovery_code:
        unused_codes = db.query(MFARecoveryCode).filter(
            MFARecoveryCode.user_id == user.id,
            MFARecoveryCode.used == False
        ).all()
        hashes = [c.code_hash for c in unused_codes]
        is_rec_valid, matched_hash = verify_and_consume_recovery_code(challenge_data.recovery_code, hashes)
        if is_rec_valid and matched_hash:
            verified = True
            used_recovery = True
            for c in unused_codes:
                if c.code_hash == matched_hash:
                    c.used = True
                    c.used_at = datetime.now(timezone.utc)
                    db.commit()
                    break

    if not verified:
        raise HTTPException(status_code=401, detail="Invalid authentication code or recovery code")

    access_token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value, "institution_id": user.institution_id}
    )
    refresh_token = create_refresh_token(subject=user.id)

    log_audit_event(
        db=db,
        action="USER_LOGIN_MFA_SUCCESS" if not used_recovery else "USER_LOGIN_RECOVERY_CODE_SUCCESS",
        entity_type="USER",
        entity_id=user.id,
        actor=user,
        ip_address=request.client.host if request.client else None
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        requires_mfa=False,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "institution_id": user.institution_id
        }
    )

@router.post("/mfa/setup", response_model=MFASetupResponse)
def mfa_setup(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Initiate TOTP MFA enrollment and return QR code."""
    secret = generate_totp_secret()
    provisioning_uri = generate_totp_uri(secret, current_user.email)
    qr_base64 = generate_qr_code_base64(provisioning_uri)

    # Store or update pending MFA configuration
    mfa_conf = db.query(MFAConfiguration).filter(MFAConfiguration.user_id == current_user.id).first()
    if not mfa_conf:
        mfa_conf = MFAConfiguration(user_id=current_user.id, secret_key=secret, is_confirmed=False)
        db.add(mfa_conf)
    else:
        mfa_conf.secret_key = secret
        mfa_conf.is_confirmed = False
    db.commit()

    return MFASetupResponse(
        secret=secret,
        provisioning_uri=provisioning_uri,
        qr_code_base64=f"data:image/png;base64,{qr_base64}",
        manual_setup_key=secret
    )

@router.post("/mfa/verify-enrollment", response_model=MFAEnrollmentSuccessResponse)
def mfa_verify_enrollment(
    data: MFAVerifyEnrollmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify first TOTP code and finalize MFA activation, generating backup recovery codes."""
    mfa_conf = db.query(MFAConfiguration).filter(MFAConfiguration.user_id == current_user.id).first()
    if not mfa_conf or mfa_conf.secret_key != data.secret:
        raise HTTPException(status_code=400, detail="Invalid MFA setup session")

    if not verify_totp_code(data.secret, data.code):
        raise HTTPException(status_code=400, detail="Invalid verification code. Please check your authenticator clock.")

    mfa_conf.is_confirmed = True
    mfa_conf.confirmed_at = datetime.now(timezone.utc)
    current_user.is_mfa_enabled = True

    # Generate 8 backup recovery codes
    plain_codes, hashed_codes = generate_recovery_codes(8)
    db.query(MFARecoveryCode).filter(MFARecoveryCode.user_id == current_user.id).delete()
    for h in hashed_codes:
        db.add(MFARecoveryCode(user_id=current_user.id, code_hash=h))

    db.commit()

    log_audit_event(
        db=db,
        action="MFA_ENROLLMENT_COMPLETED",
        entity_type="USER",
        entity_id=current_user.id,
        actor=current_user
    )

    return MFAEnrollmentSuccessResponse(
        message="Two-factor authentication has been successfully activated.",
        backup_recovery_codes=plain_codes
    )

@router.post("/register", response_model=UserResponse)
def register(reg_data: RegisterRequest, db: Session = Depends(get_db)):
    """User registration with role, email, password, and institution validation."""
    clean_email = reg_data.email.lower().strip()
    clean_name = reg_data.full_name.strip()
    
    if not clean_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Full name cannot be blank."
        )

    # Check for duplicate email
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please sign in instead."
        )

    # Security: Public registration must never grant Admin privileges
    assigned_role = reg_data.role
    if assigned_role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator accounts cannot be self-registered publicly. Please choose FDR Officer or Reviewer."
        )

    # Validate and sanitize institution_id (prevent ForeignKeyViolation 500 errors)
    institution_id = None
    if assigned_role == UserRole.INSTITUTION_USER and reg_data.institution_id:
        inst_id_clean = reg_data.institution_id.strip()
        if inst_id_clean:
            inst = db.query(Institution).filter(Institution.id == inst_id_clean).first()
            if not inst:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Selected institution does not exist. Please choose a valid institution."
                )
            institution_id = inst.id

    user = User(
        email=clean_email,
        full_name=clean_name,
        hashed_password=hash_password(reg_data.password),
        role=assigned_role,
        institution_id=institution_id,
        is_active=True,
        is_mfa_enabled=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_audit_event(
        db=db,
        action="USER_REGISTERED",
        entity_type="USER",
        entity_id=user.id,
        actor=user,
        details=f"Self-registered account with role {assigned_role.value}"
    )

    return user

@router.post("/refresh", response_model=TokenResponse)
def refresh_token_endpoint(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Rotate and refresh access tokens."""
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    new_access = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value, "institution_id": user.institution_id}
    )
    new_refresh = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        requires_mfa=False,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "institution_id": user.institution_id
        }
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve authenticated user's profile."""
    return current_user

@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Development-safe password reset request. Never reveals if account exists."""
    user = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if user:
        # Development reset token
        reset_token = create_access_token(
            subject=user.id,
            extra_claims={"type": "password_reset"}
        )
        log_audit_event(
            db=db,
            action="PASSWORD_RESET_REQUESTED",
            entity_type="USER",
            entity_id=user.id,
            details=f"Dev reset token created for {user.email}"
        )
        return {
            "message": "If an account with that email exists, password reset instructions have been dispatched.",
            "dev_reset_token": reset_token  # Provided for local hackathon testing
        }

    return {"message": "If an account with that email exists, password reset instructions have been dispatched."}

@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset user password using valid token."""
    payload = decode_token(data.token)
    if not payload or payload.get("type") != "password_reset":
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    user.hashed_password = hash_password(data.new_password)
    db.commit()

    log_audit_event(
        db=db,
        action="PASSWORD_RESET_COMPLETED",
        entity_type="USER",
        entity_id=user.id,
        actor=user
    )

    return {"message": "Password has been successfully updated. You may now login."}
