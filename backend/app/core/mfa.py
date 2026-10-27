import base64
import hashlib
import io
import os
import secrets
from typing import List, Tuple, Optional
import pyotp
import qrcode
from app.core.config import settings

def generate_totp_secret() -> str:
    """Generate a high-entropy base32 secret for TOTP."""
    return pyotp.random_base32()

def generate_totp_uri(secret: str, email: str) -> str:
    """Generate standards-compliant otpauth:// URI."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=settings.PROJECT_NAME)

def generate_qr_code_base64(provisioning_uri: str) -> str:
    """Generate a base64 encoded PNG QR code image for enrollment."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def verify_totp_code(secret: str, code: str) -> bool:
    """Verify a 6-digit TOTP code with time drift window tolerance of 1 step."""
    if not secret or not code:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code.strip(), valid_window=1)

def generate_recovery_codes(count: int = 8) -> Tuple[List[str], List[str]]:
    """
    Generate recovery codes.
    Returns:
        plain_codes: list of human-readable recovery codes (shown once to user)
        hashed_codes: list of SHA-256 hashes to store safely in DB
    """
    plain_codes = []
    hashed_codes = []
    for _ in range(count):
        code = secrets.token_hex(4).upper()  # 8 character hex code, e.g. 'A1B2C3D4'
        formatted_code = f"{code[:4]}-{code[4:]}"
        plain_codes.append(formatted_code)
        
        # Hash code for storage
        code_hash = hashlib.sha256(formatted_code.replace("-", "").strip().encode("utf-8")).hexdigest()
        hashed_codes.append(code_hash)
        
    return plain_codes, hashed_codes

def verify_and_consume_recovery_code(entered_code: str, stored_hashes: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Verify entered recovery code against list of unused hashed codes.
    Returns (True, matching_hash) if valid, (False, None) otherwise.
    """
    normalized = entered_code.replace("-", "").strip().upper()
    code_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    if code_hash in stored_hashes:
        return True, code_hash
    return False, None
