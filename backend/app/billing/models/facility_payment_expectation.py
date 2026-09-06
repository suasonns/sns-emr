from __future__ import annotations

import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

RESPONSIBILITY_CATEGORIES = {
    "HOSPICE_SERVICE",
    "ROOM_AND_BOARD",
    "BOARD_AND_LODGING",
    "FACILITY_REIMBURSEMENT",
    "SHARE_OF_COST",
    "PATIENT_RESPONSIBILITY",
    "FAMILY_CONTRIBUTION",
    "ALW_SUPPORT",
    "PRIVATE_PAY",
    "OTHER",
    "UNKNOWN",
}

FACILITY_FUNDING_SOURCES = {
    "MEDICARE",
    "MEDICAID_FFS",
    "MEDICAID_MANAGED_CARE",
    "COMMERCIAL_HMO",
    "COMMERCIAL_PPO",
    "ALW",
    "SHARE_OF_COST",
    "SOCIAL_SECURITY",
    "PATIENT_RESPONSIBILITY",
    "FAMILY_CONTRIBUTION",
    "PRIVATE_PAY",
    "COUNTY_OR_REGIONAL_ASSISTANCE",
    "FACILITY_ARRANGEMENT",
    "OTHER",
    "NOT_VERIFIED",
}

FACILITY_EXPECTATION_STATUSES = {
    "DRAFT",
    "ACTIVE",
    "SUPERSEDED",
    "CANCELLED",
    "CLOSED",
}

FACILITY_RECONCILIATION_STATUSES = {
    "NOT_EXPECTED",
    "EXPECTED",
    "NOT_BILLED",
    "BILLED",
    "PAYMENT_PENDING",
    "PARTIALLY_PAID",
    "PAID",
    "OVERPAID",
    "UNMATCHED_PAYMENT",
    "MANUAL_REVIEW_REQUIRED",
    "DENIED",
    "RECOUPED",
    "REFUNDED",
    "CLOSED",
    "NOT_VERIFIED",
}


class FacilityPaymentExpectation(Base):
    __tablename__ = "facility_payment_expectations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_pos_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patient_pos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    facility_name_snapshot = Column(String(255), nullable=True)
    residence_type_snapshot = Column(String(50), nullable=True)
    room_number_snapshot = Column(String(64), nullable=True)
    residence_start_date_snapshot = Column(Date, nullable=True)
    residence_end_date_snapshot = Column(Date, nullable=True)
    expected_funding_source_snapshot = Column(String(64), nullable=True)
    expected_payer_name_snapshot = Column(String(255), nullable=True)
    primary_payer_name_snapshot = Column(String(255), nullable=True)
    secondary_payer_name_snapshot = Column(String(255), nullable=True)

    responsibility_category = Column(String(64), nullable=False, index=True)
    expected_funding_source = Column(
        String(64),
        nullable=False,
        default="NOT_VERIFIED",
        server_default=text("'NOT_VERIFIED'"),
        index=True,
    )
    expected_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(8), nullable=False, default="USD", server_default=text("'USD'"))
    frequency = Column(String(64), nullable=True)
    service_period_start = Column(Date, nullable=False, index=True)
    service_period_end = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=True, index=True)
    authorization_reference = Column(String(255), nullable=True)
    share_of_cost_amount = Column(Numeric(12, 2), nullable=True)
    status = Column(String(32), nullable=False, default="ACTIVE", server_default=text("'ACTIVE'"), index=True)
    version_number = Column(Integer, nullable=False, default=1, server_default=text("1"))
    supersedes_expectation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("facility_payment_expectations.id", ondelete="SET NULL"),
        nullable=True,
    )
    superseded_by_expectation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("facility_payment_expectations.id", ondelete="SET NULL"),
        nullable=True,
    )
    correction_reason = Column(Text, nullable=True)
    source = Column(String(32), nullable=False, default="MANUAL", server_default=text("'MANUAL'"))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reconciliation_status = Column(
        String(32),
        nullable=False,
        default="NOT_VERIFIED",
        server_default=text("'NOT_VERIFIED'"),
        index=True,
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    tenant = relationship("Tenant")
    patient = relationship("Patient")
    patient_pos = relationship("PatientPOS")
    supersedes_expectation = relationship(
        "FacilityPaymentExpectation",
        remote_side=[id],
        foreign_keys=[supersedes_expectation_id],
        post_update=True,
    )
    superseded_by_expectation = relationship(
        "FacilityPaymentExpectation",
        remote_side=[id],
        foreign_keys=[superseded_by_expectation_id],
        post_update=True,
    )
    allocations = relationship(
        "FacilityPaymentAllocation",
        back_populates="expectation",
        cascade="all, delete-orphan",
        order_by="FacilityPaymentAllocation.created_at",
    )
    alerts = relationship("FacilityCollectionAlert", back_populates="expectation")

    __table_args__ = (
        CheckConstraint("expected_amount >= 0", name="ck_facility_payment_expectation_expected_amount_nonnegative"),
        CheckConstraint(
            "service_period_end >= service_period_start",
            name="ck_facility_payment_expectation_service_period_valid",
        ),
        Index("ix_facility_payment_expectation_tenant_patient", "tenant_id", "patient_id"),
        Index("ix_facility_payment_expectation_tenant_status", "tenant_id", "status"),
        Index(
            "ix_facility_payment_expectation_tenant_reconciliation_status",
            "tenant_id",
            "reconciliation_status",
        ),
    )
