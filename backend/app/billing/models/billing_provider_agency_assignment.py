from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.base import BaseModel

BILLING_PROVIDER_ASSIGNMENT_STATUSES = {"ACTIVE", "SUSPENDED", "TERMINATED", "PENDING"}
BILLING_PROVIDER_SERVICE_SCOPES = {
    "BILLING_READINESS",
    "CLAIMS",
    "PAYMENT_POSTING",
    "PAYMENT_RECONCILIATION",
    "FACILITY_COLLECTIONS",
    "DENIALS_APPEALS",
    "AUTHORIZATION",
    "FINANCIAL_MONITORING",
    "CAP_MONITORING",
}


class BillingProviderAgencyAssignment(BaseModel):
    __tablename__ = "billing_provider_agency_assignments"

    billing_provider_organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("billing_provider_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    relationship_status = Column(
        String(32),
        nullable=False,
        server_default=text("'PENDING'"),
        index=True,
    )

    effective_start_at = Column(DateTime(timezone=True), nullable=False)
    effective_end_at = Column(DateTime(timezone=True), nullable=True)

    # Access for an external managed-billing user requires BOTH this
    # assignment-level flag and tenants.financials_enabled to be true.
    # Keeping both allows a future assignment to be prepared before the
    # tenant-level owner toggle is switched on.
    financials_enabled = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
        default=False,
        index=True,
    )

    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    billing_provider_organization = relationship("BillingProviderOrganization")
    tenant = relationship("Tenant")
    service_scopes = relationship(
        "BillingProviderAgencyServiceScope",
        back_populates="assignment",
        cascade="all, delete-orphan",
        order_by="BillingProviderAgencyServiceScope.scope",
    )

    __table_args__ = (
        CheckConstraint(
            "relationship_status IN ('ACTIVE', 'SUSPENDED', 'TERMINATED', 'PENDING')",
            name="ck_billing_provider_assignment_relationship_status_valid",
        ),
        CheckConstraint(
            "effective_end_at IS NULL OR effective_end_at >= effective_start_at",
            name="ck_billing_provider_assignment_effective_window_valid",
        ),
        Index("ix_billing_provider_assignment_tenant_status", "tenant_id", "relationship_status"),
        Index(
            "ix_billing_provider_assignment_org_status",
            "billing_provider_organization_id",
            "relationship_status",
        ),
    )


class BillingProviderAgencyServiceScope(Base):
    __tablename__ = "billing_provider_agency_service_scopes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    assignment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("billing_provider_agency_assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    scope = Column(String(64), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    assignment = relationship("BillingProviderAgencyAssignment", back_populates="service_scopes")

    __table_args__ = (
        CheckConstraint(
            "scope IN ('BILLING_READINESS', 'CLAIMS', 'PAYMENT_POSTING', 'PAYMENT_RECONCILIATION', 'FACILITY_COLLECTIONS', 'DENIALS_APPEALS', 'AUTHORIZATION', 'FINANCIAL_MONITORING', 'CAP_MONITORING')",
            name="ck_billing_provider_assignment_scope_valid",
        ),
        UniqueConstraint("assignment_id", "scope", name="uq_billing_provider_assignment_scope"),
        Index("ix_billing_provider_scope_assignment_scope", "assignment_id", "scope"),
    )
