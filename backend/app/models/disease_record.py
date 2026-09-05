from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..database.connection import Base


class DiseaseRecord(Base):
    """
    Persistent Diagnostic & Agronomic Disease Record.
    Tracks farmer disease scan submissions through the Human-in-the-Loop (HITL)
    Field Agent review process, isolating clinical plant health from commercial marketplace listings.
    """
    __tablename__ = "disease_records"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    farmer_id = Column(
        Integer,
        ForeignKey("farmers.id"),
        nullable=False,
        index=True
    )

    crop_type = Column(
        String(100),
        nullable=False
    )

    image_url = Column(
        String(255),
        nullable=True
    )

    confidence = Column(
        Float,
        nullable=True
    )

    predicted_pathogen = Column(
        String(200),
        nullable=False
    )

    scientific_name = Column(
        String(200),
        nullable=True
    )

    severity = Column(
        String(50),
        nullable=True,
        default="moderate"
    )

    # Status Lifecycle:
    # - PENDING_AGENT_REVIEW: Initial state upon upload (prescription locked on farmer UI)
    # - VERIFIED_HEALTH_RECORD: Field Agent approved (unlocks ICAR prescription, updates crop health log)
    # - NEEDS_PHYSICAL_VISIT: Field Agent rejected/flagged (dispatches on-site agent, moves to Pending Field Visits)
    status = Column(
        String(50),
        nullable=False,
        default="PENDING_AGENT_REVIEW",
        index=True
    )

    # ICAR-Compliant Prescriptions (Unlocked upon Field Agent Approval)
    prescription_chemical = Column(
        String(255),
        nullable=True
    )

    prescription_dosage = Column(
        String(255),
        nullable=True
    )

    prescription_phi = Column(
        String(255),
        nullable=True  # Pre-Harvest Interval (e.g., "7-10 Days")
    )

    prescription_organic = Column(
        Text,
        nullable=True
    )

    # Field/Location Telemetry
    farm_area = Column(
        Float,
        nullable=True,
        default=2.5
    )

    growth_stage = Column(
        String(50),
        nullable=True
    )

    geolocation = Column(
        String(255),
        nullable=True
    )

    latitude = Column(
        Float,
        nullable=True
    )

    longitude = Column(
        Float,
        nullable=True
    )

    # Agent Audit Metadata
    agent_name = Column(
        String(100),
        nullable=True
    )

    agent_remarks = Column(
        Text,
        nullable=True
    )

    action_plan_id = Column(
        Integer,
        ForeignKey("action_plans.id"),
        nullable=True
    )

    # On-Site Field Inspection Scheduling & Farmer Response
    inspection_status = Column(
        String(50),
        nullable=True,
        default=None
    )  # SCHEDULED, CONFIRMED, RESCHEDULED, REJECTED, COMPLETED

    inspection_date = Column(
        DateTime,
        nullable=True
    )

    farmer_notes = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    verified_at = Column(
        DateTime,
        nullable=True
    )


