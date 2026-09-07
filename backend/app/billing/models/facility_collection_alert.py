from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

FACILITY_COLLECTION_ALERT_STATUSES = {
    "OPEN",
    "ACKNOWLEDGED",
    "IN_PROGRESS",
    "SNOOZED",
    "DISMISSED",
    "RESOLVED",
    "AUTO_RESOLVED",
    "SUPPRESSED",
    "EXPIRED",
}
# Non-terminal statuses are the ones an alert can still transition out of.
# The upsert-on-re-evaluation logic and auto-resolution logic both operate
# over this set. Terminal statuses (everything else) are closed permanently;
# a recurrence of the same condition creates a brand-new OPEN alert.
FACILITY_COLLECTION_ALERT_NON_TERMINAL_STATUSES = {"OPEN", "ACKNOWLEDGED", "IN_PROGRESS", "SNOOZED"}
FACILITY_COLLECTION_ALERT_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
FACILITY_COLLECTION_ALERT_DISMISSAL_REASON_CODES = {
    "FALSE_POSITIVE",
    "DUPLICATE_ALERT",
    "KNOWN_EXCEPTION",
    "BUSINESS_APPROVED",
    "OTHER",
}
# Fixed snooze presets (Architecture Spec Decision 2). Custom/arbitrary dates
# are explicitly deferred to a future version.
FACILITY_COLLECTION_ALERT_SNOOZE_PRESETS = {
    "24_HOURS": 1,
    "3_DAYS": 3,
    "7_DAYS": 7,
    "14_DAYS": 14,
    "30_DAYS": 30,
}


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
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    snoozed_until = Column(DateTime(timezone=True), nullable=True)
    dismissal_reason_code = Column(String(32), nullable=True)
    # resolution_evidence / resolved_by / resolved_at are reused as the
    # generic "closure" fields for every terminal transition (RESOLVED,
    # DISMISSED, AUTO_RESOLVED, SUPPRESSED) -- not only RESOLVED. This keeps
    # a single audited closure record per alert instead of duplicating
    # near-identical columns per terminal status.
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
