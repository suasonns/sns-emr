from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

FACILITY_COLLECTION_ALERT_STATUSES = {"OPEN", "ACKNOWLEDGED", "RESOLVED"}
FACILITY_COLLECTION_ALERT_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


class FacilityCollectionAlert(Base):
    __tablename__ = "facility_collection_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True)
    facility_payment_expectation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("facility_payment_expectations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    alert_type = Column(String(64), nullable=False, index=True)
    severity = Column(String(16), nullable=False)
    expected_amount = Column(Numeric(12, 2), nullable=True)
    received_amount = Column(Numeric(12, 2), nullable=True)
    outstanding_amount = Column(Numeric(12, 2), nullable=True)
    due_date = Column(Date, nullable=True)
    days_outstanding = Column(Integer, nullable=True)
    status = Column(String(16), nullable=False, default="OPEN", server_default=text("'OPEN'"), index=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolution_evidence = Column(Text, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    tenant = relationship("Tenant")
    patient = relationship("Patient")
    expectation = relationship("FacilityPaymentExpectation", back_populates="alerts")


class FacilityCollectionAlertThreshold(Base):
    __tablename__ = "facility_collection_alert_thresholds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alert_type = Column(String(64), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    threshold_amount = Column(Numeric(12, 2), nullable=True)
    threshold_days = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    tenant = relationship("Tenant")

    __table_args__ = (
        UniqueConstraint("tenant_id", "alert_type", name="uq_facility_collection_alert_threshold_tenant_alert"),
        Index("ix_facility_collection_alert_threshold_tenant_alert", "tenant_id", "alert_type"),
    )
