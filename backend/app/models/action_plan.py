from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from ..database.connection import Base


class ActionPlan(Base):
    __tablename__ = "action_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    listing_id = Column(
        Integer,
        ForeignKey("listings.id"),
        nullable=True
    )

    farmer_id = Column(
        Integer,
        ForeignKey("farmers.id"),
        nullable=False
    )

    crop_id = Column(String(50), nullable=True)
    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    village = Column(String(100), nullable=True)
    planting_date = Column(String(50), nullable=True)
    crop_stage = Column(String(100), nullable=True)

    risk_type = Column(
        String(100),
        nullable=False,
        default="disease_treatment"
    )

    risk_level = Column(
        String(50),
        nullable=False,
        default="moderate"
    )

    status = Column(
        String(50),
        nullable=False,
        default="active"
    )

    escalation_required = Column(Boolean, default=False, nullable=False)
    escalation_reason = Column(Text, nullable=True)
    recommendation_json = Column(Text, nullable=True)

    decision_json = Column(Text, nullable=True)  # Serialized MultiSignalDecision
    constraints_json = Column(Text, nullable=True)  # Serialized constraints / blocked actions
    recommended_actions_json = Column(Text, nullable=True)  # Serialized allowed actions
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    tasks = relationship(
        "PlanTask",
        back_populates="action_plan",
        cascade="all, delete-orphan",
        order_by="PlanTask.id"
    )

    calendar_events = relationship(
        "CalendarEvent",
        back_populates="action_plan",
        cascade="all, delete-orphan",
        order_by="CalendarEvent.id"
    )

    notifications = relationship(
        "NotificationEvent",
        back_populates="action_plan",
        cascade="all, delete-orphan",
        order_by="NotificationEvent.id"
    )

    escalations = relationship(
        "FieldAgentEscalation",
        back_populates="action_plan",
        cascade="all, delete-orphan",
        order_by="FieldAgentEscalation.id"
    )


class PlanTask(Base):
    __tablename__ = "plan_tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    action_plan_id = Column(
        Integer,
        ForeignKey("action_plans.id"),
        nullable=False
    )

    title = Column(
        String(255),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    location = Column(
        String(255),
        nullable=True
    )

    execution_window = Column(
        String(255),
        nullable=True
    )

    scheduled_for = Column(
        DateTime,
        nullable=True
    )

    status = Column(
        String(50),
        nullable=False,
        default="pending"
    )

    reasoning = Column(
        Text,
        nullable=True
    )

    completed_at = Column(
        DateTime,
        nullable=True
    )

    action_plan = relationship(
        "ActionPlan",
        back_populates="tasks"
    )


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    action_plan_id = Column(
        Integer,
        ForeignKey("action_plans.id"),
        nullable=False
    )

    farmer_id = Column(
        Integer,
        nullable=False
    )

    event_id = Column(String(100), nullable=True)
    crop_id = Column(String(50), nullable=True)
    stage_name = Column(String(100), nullable=True)
    activity_type = Column(String(100), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    scheduled_date = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="scheduled")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    action_plan = relationship(
        "ActionPlan",
        back_populates="calendar_events"
    )


class NotificationEvent(Base):
    __tablename__ = "notification_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    action_plan_id = Column(
        Integer,
        ForeignKey("action_plans.id"),
        nullable=True
    )

    farmer_id = Column(
        Integer,
        nullable=False
    )

    notification_id = Column(String(100), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=True, default="SYSTEM")  # TREATMENT_APPROVED, INSPECTION_DISPATCHED, WEATHER_ALERT, ORDER, SYSTEM
    related_id = Column(Integer, nullable=True)
    action_url = Column(String(255), nullable=True)
    meta_data = Column(Text, nullable=True)  # JSON metadata payload
    channel = Column(String(50), default="sms_voice_app", nullable=False)
    priority = Column(String(50), default="medium", nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, NOTIFIED, ACKNOWLEDGED, IN_PROGRESS, COMPLETED, SKIPPED, ESCALATED, READ

    scheduled_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    action_plan = relationship(
        "ActionPlan",
        back_populates="notifications"
    )


class FieldAgentEscalation(Base):
    __tablename__ = "field_agent_escalations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    action_plan_id = Column(
        Integer,
        ForeignKey("action_plans.id"),
        nullable=False
    )

    farmer_id = Column(
        Integer,
        nullable=False
    )

    field_agent_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    risk_level = Column(String(50), nullable=False, default="high")
    reason = Column(Text, nullable=False)
    status = Column(String(50), default="escalated", nullable=False)  # escalated, assigned, visited, resolved
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    action_plan = relationship(
        "ActionPlan",
        back_populates="escalations"
    )
