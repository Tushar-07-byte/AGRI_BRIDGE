from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, text
from ..database.connection import Base


class OTPVerification(Base):
    __tablename__ = "otp_verifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    mobile = Column(String(20), index=True, nullable=False)
    otp_hash = Column(String(255), nullable=False)
    purpose = Column(String(50), default="login", nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def has_exceeded_attempts(self, max_attempts: int = 5) -> bool:
        return self.attempts >= max_attempts

