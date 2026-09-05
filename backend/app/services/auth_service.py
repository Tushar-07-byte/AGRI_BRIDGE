import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..models.user import User

# JWT / Secret Key Config
AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "agribridge_super_secure_jwt_secret_key_2026")
TOKEN_EXPIRY_HOURS = int(os.getenv("TOKEN_EXPIRY_HOURS", "24"))
OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "5"))
MAX_OTP_ATTEMPTS = int(os.getenv("MAX_OTP_ATTEMPTS", "5"))
OTP_RESEND_COOLDOWN_SECONDS = int(os.getenv("OTP_RESEND_COOLDOWN_SECONDS", "30"))

# Role constants
ROLE_FARMER = "farmer"
ROLE_BUYER = "buyer"
ROLE_FIELD_AGENT = "field-agent"
ROLE_PROFESSIONAL_ALIAS = "professional"
ROLE_FIELD_AGENT_UNDERSCORE = "field_agent"

ROLE_ALIASES = {
    "farmer": ROLE_FARMER,
    "buyer": ROLE_BUYER,
    "field-agent": ROLE_FIELD_AGENT,
    "field_agent": ROLE_FIELD_AGENT,
    "professional": ROLE_FIELD_AGENT,
}

VALID_ROLES = set(ROLE_ALIASES.keys())
CANONICAL_ROLES = {ROLE_FARMER, ROLE_BUYER, ROLE_FIELD_AGENT}

ROLE_REDIRECT_MAP = {
    ROLE_FARMER: "/frontend/pages/farmer-dashboard.html",
    ROLE_BUYER: "/frontend/pages/buyer-dashboard.html",
    ROLE_FIELD_AGENT: "/frontend/pages/field-agent-dashboard.html",
    "professional": "/frontend/pages/field-agent-dashboard.html",
    "field_agent": "/frontend/pages/field-agent-dashboard.html",
}


# ==============================================================================
# 1. MOBILE NUMBER NORMALIZATION
# ==============================================================================

def normalize_mobile(mobile: str) -> str:
    """
    Normalizes any mobile string to canonical format +91XXXXXXXXXX.
    Supports 9876543210, +919876543210, 919876543210, 09876543210, with spaces/hyphens.
    """
    if not mobile:
        raise ValueError("Mobile number is required.")

    # Remove all non-numeric characters except leading +
    cleaned = re.sub(r"[^\d+]", "", mobile.strip())

    # Strip leading +
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]

    # Remove leading 0
    if cleaned.startswith("0") and len(cleaned) == 11:
        cleaned = cleaned[1:]

    # Remove leading country code 91 if 12 digits
    if cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]

    # Must now be exactly 10 digits
    if len(cleaned) != 10 or not cleaned.isdigit():
        raise ValueError("Invalid Indian mobile number. Must be 10 digits.")

    # Validate first digit (Indian mobile numbers start with 6, 7, 8, 9)
    if cleaned[0] not in "6789":
        raise ValueError("Invalid Indian mobile number. Must start with 6, 7, 8, or 9.")

    return f"+91{cleaned}"


# ==============================================================================
# 2. PASSWORD SECURITY (PBKDF2-HMAC-SHA256)
# ==============================================================================

def hash_password(password: str) -> str:
    """
    Hashes password using PBKDF2-HMAC-SHA256 with 100,000 iterations and a 32-byte salt.
    Format: pbkdf2:sha256:100000$<salt_hex>$<hash_hex>
    """
    if not password:
        raise ValueError("Password cannot be empty.")

    salt = secrets.token_bytes(32)
    iterations = 100_000
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    
    salt_hex = salt.hex()
    hash_hex = derived.hex()
    return f"pbkdf2:sha256:{iterations}${salt_hex}${hash_hex}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against the stored PBKDF2 hash using constant-time comparison.
    """
    if not plain_password or not hashed_password:
        return False

    try:
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False

        header, salt_hex, hash_hex = parts
        _, _, iter_str = header.split(":")
        iterations = int(iter_str)
        salt = bytes.fromhex(salt_hex)

        derived = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(derived.hex(), hash_hex)
    except Exception:
        return False


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validates that password is at least 8 characters.
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    return True, "Password is valid."


# ==============================================================================
# 3. OTP ENGINE (CRYPTOGRAPHIC 6-DIGIT WITH SHA256 HASH)
# ==============================================================================

def generate_otp() -> str:
    """
    Generates a cryptographically secure 6-digit numeric OTP (100000 - 999999).
    """
    return str(secrets.randbelow(900_000) + 100_000)


def hash_otp(otp: str, mobile: str) -> str:
    """
    Hashes OTP with HMAC-SHA256 bound to the canonical mobile number.
    """
    key = AUTH_SECRET_KEY.encode("utf-8")
    msg = f"{mobile}:{otp}".encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def verify_otp_hash(plain_otp: str, mobile: str, hashed_otp: str) -> bool:
    """
    Verifies plain OTP against stored hash using constant-time comparison.
    """
    expected_hash = hash_otp(plain_otp, mobile)
    return hmac.compare_digest(expected_hash, hashed_otp)


# ==============================================================================
# 4. JWT / SESSION TOKEN ENGINE (HMAC-SHA256 SIGNED)
# ==============================================================================

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    padding = "=" * (4 - (len(s) % 4)) if len(s) % 4 != 0 else ""
    return base64.urlsafe_b64decode(s + padding)


def create_access_token(user_id: int, mobile: str, name: str, role: str, expires_delta_hours: int = TOKEN_EXPIRY_HOURS) -> str:
    """
    Creates a signed JWT-style token containing user identity and expiry.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    exp_timestamp = int(time.time()) + (expires_delta_hours * 3600)
    
    payload = {
        "sub": str(user_id),
        "user_id": user_id,
        "mobile": mobile,
        "name": name,
        "role": role,
        "exp": exp_timestamp,
        "iat": int(time.time()),
    }

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

    signature = hmac.new(
        AUTH_SECRET_KEY.encode("utf-8"),
        f"{header_b64}.{payload_b64}".encode("utf-8"),
        hashlib.sha256
    ).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodes and validates a signed JWT token. Returns payload dict or None if invalid/expired.
    """
    if not token or not isinstance(token, str):
        return None

    parts = token.split(".")
    if len(parts) != 3:
        return None

    header_b64, payload_b64, sig_b64 = parts

    # Verify signature
    expected_sig = hmac.new(
        AUTH_SECRET_KEY.encode("utf-8"),
        f"{header_b64}.{payload_b64}".encode("utf-8"),
        hashlib.sha256
    ).digest()

    if not hmac.compare_digest(_b64url_encode(expected_sig), sig_b64):
        return None

    try:
        payload_json = _b64url_decode(payload_b64).decode("utf-8")
        payload = json.loads(payload_json)

        # Check expiry
        if "exp" in payload and payload["exp"] < int(time.time()):
            return None

        return payload
    except Exception:
        return None


# ==============================================================================
# 5. FASTAPI AUTHENTICATION DEPENDENCY
# ==============================================================================

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to extract and authenticate the current user from Authorization: Bearer <token>.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    payload = decode_access_token(token)
    if not payload or "user_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_role(allowed_roles: List[str]):
    """
    Dependency factory to enforce role-based authorization on protected routes.
    """
    canonical_allowed = {ROLE_ALIASES.get(r.lower(), r.lower()) for r in allowed_roles}

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = (current_user.role or "").lower()
        canonical_user_role = ROLE_ALIASES.get(user_role, user_role)
        if canonical_user_role not in canonical_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of roles: {list(canonical_allowed)}.",
            )
        return current_user

    return role_checker

