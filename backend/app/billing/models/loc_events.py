# app/billing/models/loc_events.py

from __future__ import annotations

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
from sqlalchemy.orm import relationship

from app.db.base import Base


class HospiceServiceLevel(str, Enum):
    """
    Canonical hospice levels of care for SNS EMR.

    CMS hospice payment categories include:
    - General inpatient care
    - Inpatient respite care
    - Continuous home care
    - Routine home care

    This model file covers the non-routine levels represented by these tables.
    """
    GIP = "GIP"
    RESPITE = "RESPITE"
    CONTINUOUS_CARE = "CONTINUOUS_CARE"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GIPPeriod(Base):
    __tablename__ = "gip_periods"

    id = Column(String, primary_key=True)

    tenant_id = Column(String, nullable=True, index=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    visit_id = Column(String, ForeignKey("visits.id"), nullable=True, index=True)

    service_level = Column(String, nullable=False, default=HospiceServiceLevel.GIP.value)
    status = Column(String, nullable=False, default="ACTIVE")

    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)

    reason = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id])
    visit = relationship("Visit", foreign_keys=[visit_id])

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_gip_period_dates"),
        Index("ix_gip_period_patient_service_dates", "patient_id", "service_level", "start_date", "end_date"),
    )


class RespitePeriod(Base):
    __tablename__ = "respite_periods"

    id = Column(String, primary_key=True)

    tenant_id = Column(String, nullable=True, index=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    visit_id = Column(String, ForeignKey("visits.id"), nullable=True, index=True)

    service_level = Column(String, nullable=False, default=HospiceServiceLevel.RESPITE.value)
    status = Column(String, nullable=False, default="ACTIVE")

    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)

    reason = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id])
    visit = relationship("Visit", foreign_keys=[visit_id])

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_respite_period_dates"),
        Index("ix_respite_period_patient_service_dates", "patient_id", "service_level", "start_date", "end_date"),
    )


class ContinuousCareEvent(Base):
    __tablename__ = "continuous_care_events"

    id = Column(String, primary_key=True)

    tenant_id = Column(String, nullable=True, index=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    visit_id = Column(String, ForeignKey("visits.id"), nullable=True, index=True)

    service_level = Column(String, nullable=False, default=HospiceServiceLevel.CONTINUOUS_CARE.value)
    status = Column(String, nullable=False, default="ACTIVE")

    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)

    reason = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id])
    visit = relationship("Visit", foreign_keys=[visit_id])

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_continuous_care_event_dates"),
        Index("ix_continuous_care_patient_service_dates", "patient_id", "service_level", "start_date", "end_date"),
    )