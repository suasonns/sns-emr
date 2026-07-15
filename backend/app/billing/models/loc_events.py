# app/billing/models/loc_events.py

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class HospiceServiceLevel(str, Enum):
    GIP = "GIP"
    RESPITE = "RESPITE"
    CONTINUOUS_CARE = "CONTINUOUS_CARE"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------
# GIP PERIOD
# ---------------------------------------------------------
class GIPPeriod(Base):
    __tablename__ = "gip_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id"), nullable=True, index=True)

    service_level = Column(String(32), nullable=False, default=HospiceServiceLevel.GIP.value)
    status = Column(String(32), nullable=False, default="ACTIVE")

    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)

    reason = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id])
    visit = relationship("Visit", foreign_keys=[visit_id])

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_gip_period_dates"),
        Index("ix_gip_period_patient_service_dates", "patient_id", "service_level", "start_date", "end_date"),
    )


# ---------------------------------------------------------
# RESPITE PERIOD
# ---------------------------------------------------------
class RespitePeriod(Base):
    __tablename__ = "respite_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id"), nullable=True, index=True)

    service_level = Column(String(32), nullable=False, default=HospiceServiceLevel.RESPITE.value)
    status = Column(String(32), nullable=False, default="ACTIVE")

    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)

    reason = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id])
    visit = relationship("Visit", foreign_keys=[visit_id])

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_respite_period_dates"),
        Index("ix_respite_period_patient_service_dates", "patient_id", "service_level", "start_date", "end_date"),
    )


# ---------------------------------------------------------
# CONTINUOUS CARE EVENT
# ---------------------------------------------------------
class ContinuousCareEvent(Base):
    __tablename__ = "continuous_care_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id"), nullable=True, index=True)

    service_level = Column(String(32), nullable=False, default=HospiceServiceLevel.CONTINUOUS_CARE.value)
    status = Column(String(32), nullable=False, default="ACTIVE")

    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)

    reason = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id])
    visit = relationship("Visit", foreign_keys=[visit_id])

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_continuous_care_event_dates"),
        Index("ix_continuous_care_patient_service_dates", "patient_id", "service_level", "start_date", "end_date"),
    )