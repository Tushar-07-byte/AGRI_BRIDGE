from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from ..database.connection import Base


class Verification(Base):

    __tablename__ = "verifications"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    listing_id = Column(
        Integer,
        ForeignKey("listings.id"),
        nullable=False
    )

    agent_name = Column(
        String(100),
        nullable=True
    )

    status = Column(
        String(50),
        nullable=False,
        default="pending"
    )

    remarks = Column(
        String(500),
        nullable=True
    )

    verified_at = Column(
        DateTime,
        nullable=True
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )