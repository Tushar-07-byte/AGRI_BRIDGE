import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..models.user import User
from ..models.otp import OTPVerification
from ..models.farmer import Farmer
from ..models.buyer import Buyer
from ..schema.auth import (
    RegisterRequest,
    LoginRequest,
    SendOTPRequest,
    VerifyOTPRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    AuthResponse,
)
from ..services.auth_service import (
    normalize_mobile,
    hash_password,
    verify_password,
    validate_password_strength,
    generate_otp,
    hash_otp,
    verify_otp_hash,
    create_access_token,
    get_current_user,
    ROLE_FARMER,
    ROLE_BUYER,
    ROLE_FIELD_AGENT,
    ROLE_ALIASES,
    VALID_ROLES,
    CANONICAL_ROLES,
    ROLE_REDIRECT_MAP,
    OTP_EXPIRY_MINUTES,
    OTP_RESEND_COOLDOWN_SECONDS,
    MAX_OTP_ATTEMPTS,
)

logger = logging.getLogger("agribridge.auth")

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


# ==============================================================================
# 1. REGISTRATION
# ==============================================================================

@router.post("/register", response_model=AuthResponse)
def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user (Farmer, Buyer, or Field Agent) with mobile + password.
    """
    # 1. Normalize Mobile
    try:
        canonical_mobile = normalize_mobile(req.mobile)
    except ValueError as e:
        return AuthResponse(
            success=False,
            code="INVALID_MOBILE",
            message=str(e)
        )

    # 2. Validate & Normalize Role to Canonical Format
    raw_role = req.role.strip().lower()
    if raw_role not in VALID_ROLES:
        return AuthResponse(
            success=False,
            code="INVALID_ROLE",
            message=f"Invalid role. Must be one of: {list(CANONICAL_ROLES)}"
        )
    
    # Normalize to canonical role ('field-agent', 'farmer', 'buyer')
    role = ROLE_ALIASES.get(raw_role, ROLE_FIELD_AGENT)

    # 3. Validate Password Strength
    is_valid, msg = validate_password_strength(req.password)
    if not is_valid:
        return AuthResponse(
            success=False,
            code="WEAK_PASSWORD",
            message=msg
        )

    if req.confirm_password and req.password != req.confirm_password:
        return AuthResponse(
            success=False,
            code="PASSWORD_MISMATCH",
            message="Password and confirm password do not match."
        )

    # 4. Check for Existing Account
    existing_user = db.query(User).filter(User.mobile == canonical_mobile).first()
    if existing_user:
        return AuthResponse(
            success=False,
            code="ACCOUNT_EXISTS",
            message="This mobile number is already registered with an AgriBridge account."
        )

    # 5. Hash Password & Create User
    pwd_hash = hash_password(req.password)
    new_user = User(
        name=req.name.strip(),
        email=req.email.strip() if req.email else None,
        mobile=canonical_mobile,
        password_hash=pwd_hash,
        role=role,
        is_verified=True,
        last_login_at=None
    )
    db.add(new_user)
    db.flush()  # assign new_user.id

    # 6. Ensure Compatibility with Legacy Farmers & Buyers Tables
    if role == ROLE_FARMER:
        existing_farmer = db.query(Farmer).filter(Farmer.name == new_user.name).first()
        if not existing_farmer:
            db.add(Farmer(name=new_user.name))
    elif role == ROLE_BUYER:
        existing_buyer = db.query(Buyer).filter(Buyer.name == new_user.name).first()
        if not existing_buyer:
            db.add(Buyer(name=new_user.name))

    db.commit()
    db.refresh(new_user)

    # 7. Direct user to Login page (Registration and Login are separate operations)
    redirect_url = f"/frontend/pages/login.html?registered=true&mobile={canonical_mobile}"

    return AuthResponse(
        success=True,
        message="Registration successful! Please log in with your credentials.",
        token=None,
        user=None,
        redirect=redirect_url
    )


# ==============================================================================
# 2. LOGIN (PASSWORD)
# ==============================================================================

@router.post("/login", response_model=AuthResponse)
def login_user(
    req: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user using mobile + password.
    """
    try:
        canonical_mobile = normalize_mobile(req.mobile)
    except ValueError as e:
        return AuthResponse(
            success=False,
            code="INVALID_MOBILE",
            message=str(e)
        )

    user = db.query(User).filter(User.mobile == canonical_mobile).first()
    if not user:
        return AuthResponse(
            success=False,
            code="USER_NOT_FOUND",
            message="No account found with this mobile number."
        )

    if not verify_password(req.password, user.password_hash):
        return AuthResponse(
            success=False,
            code="INVALID_CREDENTIALS",
            message="Incorrect mobile number or password."
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    token = create_access_token(
        user_id=user.id,
        mobile=user.mobile,
        name=user.name,
        role=user.role
    )

    redirect_url = ROLE_REDIRECT_MAP.get(user.role, "/frontend/pages/farmer-dashboard.html")

    return AuthResponse(
        success=True,
        message="Login successful! Redirecting to your dashboard.",
        token=token,
        user=user.to_dict(),
        redirect=redirect_url
    )


# ==============================================================================
# 3. SEND OTP (LOGIN / FORGOT PASSWORD / REGISTRATION)
# ==============================================================================

@router.post("/send-otp")
def send_otp(
    req: SendOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Generate and dispatch a cryptographically secure 6-digit OTP (5-minute expiry).
    """
    try:
        canonical_mobile = normalize_mobile(req.mobile)
    except ValueError as e:
        return {
            "success": False,
            "code": "INVALID_MOBILE",
            "message": str(e)
        }

    purpose = (req.purpose or "login").strip().lower()

    # Check user existence according to purpose
    user = db.query(User).filter(User.mobile == canonical_mobile).first()
    if purpose in ["login", "forgot_password"] and not user:
        return {
            "success": False,
            "code": "USER_NOT_FOUND",
            "message": "No account found with this mobile number."
        }

    # Rate Limiting: 30s Cooldown
    now = datetime.utcnow()
    recent_otp = db.query(OTPVerification).filter(
        OTPVerification.mobile == canonical_mobile,
        OTPVerification.created_at >= now - timedelta(seconds=OTP_RESEND_COOLDOWN_SECONDS)
    ).first()

    if recent_otp:
        return {
            "success": False,
            "code": "RATE_LIMITED",
            "message": f"Please wait {OTP_RESEND_COOLDOWN_SECONDS} seconds before requesting a new OTP."
        }

    # Invalidate prior unused OTPs for this mobile
    db.query(OTPVerification).filter(
        OTPVerification.mobile == canonical_mobile,
        OTPVerification.used == False
    ).update({"used": True})

    # Generate 6-digit OTP
    plain_otp = generate_otp()
    otp_hashed = hash_otp(plain_otp, canonical_mobile)
    expires_at = now + timedelta(minutes=OTP_EXPIRY_MINUTES)

    new_otp_rec = OTPVerification(
        mobile=canonical_mobile,
        otp_hash=otp_hashed,
        purpose=purpose,
        expires_at=expires_at,
        attempts=0,
        used=False,
        created_at=now
    )
    db.add(new_otp_rec)
    db.commit()

    # In Production: dispatch via SMS gateway (Twilio / Fast2SMS / MSG91)
    # In Development / Demo: Log and provide transparent development code
    logger.info(f"[DEV OTP] Mobile: {canonical_mobile} | OTP: {plain_otp} | Purpose: {purpose} | Expires in: 5 min")

    return {
        "success": True,
        "message": f"6-digit OTP sent successfully to {canonical_mobile[:5]}XXXX{canonical_mobile[-2:]}.",
        "expires_in_seconds": OTP_EXPIRY_MINUTES * 60,
        "dev_otp": plain_otp  # Development / Hackathon Evaluation Helper
    }


# ==============================================================================
# 4. VERIFY OTP (LOGIN)
# ==============================================================================

@router.post("/verify-otp", response_model=AuthResponse)
def verify_otp(
    req: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Verify OTP and log user into their role-specific dashboard.
    """
    try:
        canonical_mobile = normalize_mobile(req.mobile)
    except ValueError as e:
        return AuthResponse(
            success=False,
            code="INVALID_MOBILE",
            message=str(e)
        )

    # Fetch latest active OTP
    otp_rec = db.query(OTPVerification).filter(
        OTPVerification.mobile == canonical_mobile,
        OTPVerification.used == False
    ).order_by(OTPVerification.id.desc()).first()

    if not otp_rec:
        return AuthResponse(
            success=False,
            code="INVALID_OTP",
            message="No active OTP found. Please request a new OTP."
        )

    # Check Expiry
    if otp_rec.is_expired():
        otp_rec.used = True
        db.commit()
        return AuthResponse(
            success=False,
            code="OTP_EXPIRED",
            message="OTP has expired. Please request a new one."
        )

    # Check Attempt Limit
    if otp_rec.has_exceeded_attempts(MAX_OTP_ATTEMPTS):
        otp_rec.used = True
        db.commit()
        return AuthResponse(
            success=False,
            code="MAX_ATTEMPTS_EXCEEDED",
            message="Maximum verification attempts exceeded. Please request a new OTP."
        )

    # Verify Hash
    if not verify_otp_hash(req.otp.strip(), canonical_mobile, otp_rec.otp_hash):
        otp_rec.attempts += 1
        db.commit()
        remaining = MAX_OTP_ATTEMPTS - otp_rec.attempts
        return AuthResponse(
            success=False,
            code="INVALID_OTP",
            message=f"Incorrect OTP. {remaining} attempt(s) remaining."
        )

    # Mark OTP as used
    otp_rec.used = True

    # Lookup user
    user = db.query(User).filter(User.mobile == canonical_mobile).first()
    if not user:
        db.commit()
        return AuthResponse(
            success=False,
            code="USER_NOT_FOUND",
            message="No account found with this mobile number. Please sign up."
        )

    user.last_login_at = datetime.utcnow()
    db.commit()

    token = create_access_token(
        user_id=user.id,
        mobile=user.mobile,
        name=user.name,
        role=user.role
    )

    redirect_url = ROLE_REDIRECT_MAP.get(user.role, "/frontend/pages/farmer-dashboard.html")

    return AuthResponse(
        success=True,
        message="OTP verified successfully! Welcome back.",
        token=token,
        user=user.to_dict(),
        redirect=redirect_url
    )


# ==============================================================================
# 5. FORGOT PASSWORD & RESET FLOW
# ==============================================================================

@router.post("/forgot-password")
def forgot_password(
    req: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Initiate password reset flow by dispatching reset OTP.
    """
    return send_otp(SendOTPRequest(mobile=req.mobile, purpose="forgot_password"), db)


@router.post("/verify-reset-otp")
def verify_reset_otp(
    req: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Validates reset OTP without performing login.
    """
    try:
        canonical_mobile = normalize_mobile(req.mobile)
    except ValueError as e:
        return {"success": False, "code": "INVALID_MOBILE", "message": str(e)}

    otp_rec = db.query(OTPVerification).filter(
        OTPVerification.mobile == canonical_mobile,
        OTPVerification.used == False,
        OTPVerification.purpose == "forgot_password"
    ).order_by(OTPVerification.id.desc()).first()

    if not otp_rec or otp_rec.is_expired():
        return {"success": False, "code": "INVALID_OTP", "message": "Invalid or expired OTP."}

    if not verify_otp_hash(req.otp.strip(), canonical_mobile, otp_rec.otp_hash):
        otp_rec.attempts += 1
        db.commit()
        return {"success": False, "code": "INVALID_OTP", "message": "Incorrect OTP."}

    return {"success": True, "message": "OTP verified. Proceed to set your new password."}


@router.post("/reset-password", response_model=AuthResponse)
def reset_password(
    req: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Verify reset OTP and update user's password hash.
    """
    try:
        canonical_mobile = normalize_mobile(req.mobile)
    except ValueError as e:
        return AuthResponse(success=False, code="INVALID_MOBILE", message=str(e))

    # Validate new password
    is_valid, msg = validate_password_strength(req.new_password)
    if not is_valid:
        return AuthResponse(success=False, code="WEAK_PASSWORD", message=msg)

    if req.confirm_password and req.new_password != req.confirm_password:
        return AuthResponse(success=False, code="PASSWORD_MISMATCH", message="Passwords do not match.")

    # Validate OTP
    otp_rec = db.query(OTPVerification).filter(
        OTPVerification.mobile == canonical_mobile,
        OTPVerification.used == False,
        OTPVerification.purpose == "forgot_password"
    ).order_by(OTPVerification.id.desc()).first()

    if not otp_rec or otp_rec.is_expired():
        return AuthResponse(success=False, code="INVALID_OTP", message="Reset OTP is invalid or has expired.")

    if not verify_otp_hash(req.otp.strip(), canonical_mobile, otp_rec.otp_hash):
        otp_rec.attempts += 1
        db.commit()
        return AuthResponse(success=False, code="INVALID_OTP", message="Incorrect reset OTP.")

    user = db.query(User).filter(User.mobile == canonical_mobile).first()
    if not user:
        return AuthResponse(success=False, code="USER_NOT_FOUND", message="No user found for this mobile number.")

    # Update password hash
    user.password_hash = hash_password(req.new_password)
    user.updated_at = datetime.utcnow()
    otp_rec.used = True
    db.commit()

    return AuthResponse(
        success=True,
        message="Password updated successfully! You can now log in.",
        redirect="/frontend/pages/login.html"
    )


# ==============================================================================
# 6. GET CURRENT USER & LOGOUT
# ==============================================================================

@router.get("/me")
def get_authenticated_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve authenticated user profile and active role.
    """
    return {
        "success": True,
        "user": current_user.to_dict()
    }


@router.post("/logout")
def logout_user():
    """
    Acknowledge user logout.
    """
    return {
        "success": True,
        "message": "Logged out successfully."
    }


from pydantic import BaseModel

class DemoLoginRequest(BaseModel):
    role: str

@router.post("/demo-login")
def demo_login(req: DemoLoginRequest, db: Session = Depends(get_db)):
    """
    1-click instant demo login for hackathon judges across all 3 roles:
    farmer, buyer, field-agent.
    """
    raw_role = (req.role or "farmer").strip().lower()
    role = ROLE_ALIASES.get(raw_role, ROLE_FARMER)

    demo_profiles = {
        ROLE_FARMER: {"name": "Farmer Ramesh", "mobile": "+919876500001"},
        ROLE_BUYER: {"name": "AgroCorp Buyer", "mobile": "+919876500002"},
        ROLE_FIELD_AGENT: {"name": "Field Agent Vikram", "mobile": "+919876500003"}
    }

    profile = demo_profiles.get(role, demo_profiles[ROLE_FARMER])
    canonical_mobile = profile["mobile"]

    user = db.query(User).filter(User.mobile == canonical_mobile).first()
    if not user:
        user = User(
            name=profile["name"],
            mobile=canonical_mobile,
            password_hash=hash_password("DemoPass123!"),
            role=role,
            is_verified=True,
            last_login_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.role = role
        user.last_login_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

    token = create_access_token(
        user_id=user.id,
        mobile=user.mobile,
        name=user.name,
        role=user.role
    )

    redirect_url = ROLE_REDIRECT_MAP.get(role, "/frontend/pages/farmer-dashboard.html")

    return {
        "success": True,
        "token": token,
        "user": user.to_dict(),
        "redirect": redirect_url
    }


