from __future__ import annotations

import uuid

from sqlalchemy import (
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
    "NOE_TRACKING",
    "ELIGIBILITY",
    "AUTHORIZATION_TRACKING",
    "PAYMENT_POSTING",
    "PAYMENT_RECONCILIATION",
    "FACILITY_COLLECTIONS",
    "CREDIT_BALANCES",
    "AGING_REPORT",
    "DENIALS_APPEALS",
    "EDI",
    "BILLING_REPORTS",
    "FINANCIAL_MONITORING",
    "CAP_MONITORING",
}
BILLING_PROVIDER_PERMISSION_LEVELS = {"VIEW", "EDIT"}


def normalize_billing_provider_service_scope(scope: str) -> str:
    normalized = (scope or "").strip().upper()
    if normalized not in BILLING_PROVIDER_SERVICE_SCOPES:
        raise ValueError(
            f"service scope must be one of {sorted(BILLING_PROVIDER_SERVICE_SCOPES)}"
        )
    return normalized


def normalize_billing_provider_permission_level(permission_level: str | None) -> str:
    normalized = (permission_level or "VIEW").strip().upper()
    if normalized not in BILLING_PROVIDER_PERMISSION_LEVELS:
        raise ValueError(
            f"permission level must be one of {sorted(BILLING_PROVIDER_PERMISSION_LEVELS)}"
        )
    return normalized


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
    permission_level = Column(
        String(16),
        nullable=False,
        server_default=text("'VIEW'"),
    )

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    assignment = relationship("BillingProviderAgencyAssignment", back_populates="service_scopes")

    __table_args__ = (
        CheckConstraint(
            "scope IN ('BILLING_READINESS', 'CLAIMS', 'NOE_TRACKING', 'ELIGIBILITY', 'AUTHORIZATION_TRACKING', 'PAYMENT_POSTING', 'PAYMENT_RECONCILIATION', 'FACILITY_COLLECTIONS', 'CREDIT_BALANCES', 'AGING_REPORT', 'DENIALS_APPEALS', 'EDI', 'BILLING_REPORTS', 'CAP_MONITORING', 'FINANCIAL_MONITORING')",
            name="ck_billing_provider_assignment_scope_valid",
        ),
        CheckConstraint(
            "permission_level IN ('VIEW', 'EDIT')",
            name="ck_billing_provider_assignment_permission_level_valid",
        ),
        UniqueConstraint("assignment_id", "scope", name="uq_billing_provider_assignment_scope"),
        Index("ix_billing_provider_scope_assignment_scope", "assignment_id", "scope"),
    )
