from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    email: Optional[str] = None
    mobile: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=8)
    confirm_password: Optional[str] = None
    role: str = Field(default="farmer")


class LoginRequest(BaseModel):
    mobile: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=1)


class SendOTPRequest(BaseModel):
    mobile: str = Field(..., min_length=10, max_length=20)
    purpose: Optional[str] = Field(default="login")


class VerifyOTPRequest(BaseModel):
    mobile: str = Field(..., min_length=10, max_length=20)
    otp: str = Field(..., min_length=6, max_length=6)


class ForgotPasswordRequest(BaseModel):
    mobile: str = Field(..., min_length=10, max_length=20)


class ResetPasswordRequest(BaseModel):
    mobile: str = Field(..., min_length=10, max_length=20)
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8)
    confirm_password: Optional[str] = None


class AuthResponse(BaseModel):
    success: bool
    message: str
    code: Optional[str] = None
    token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
    redirect: Optional[str] = None

