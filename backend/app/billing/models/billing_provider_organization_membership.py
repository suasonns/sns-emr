from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel

BILLING_PROVIDER_MEMBERSHIP_ROLES = {"MEMBER", "ADMIN"}
BILLING_PROVIDER_MEMBERSHIP_STATUSES = {"ACTIVE", "INACTIVE", "SUSPENDED"}


class BillingProviderOrganizationMembership(BaseModel):
    __tablename__ = "billing_provider_organization_memberships"

    billing_provider_organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("billing_provider_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    membership_role = Column(
        String(32),
        nullable=False,
        server_default=text("'MEMBER'"),
    )

    status = Column(
        String(32),
        nullable=False,
        server_default=text("'ACTIVE'"),
    )

    effective_start_at = Column(DateTime(timezone=True), nullable=False)
    effective_end_at = Column(DateTime(timezone=True), nullable=True)

    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            "membership_role IN ('MEMBER', 'ADMIN')",
            name="ck_billing_provider_membership_role_valid",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')",
            name="ck_billing_provider_membership_status_valid",
        ),
        CheckConstraint(
            "effective_end_at IS NULL OR effective_end_at >= effective_start_at",
            name="ck_billing_provider_membership_effective_window_valid",
        ),
        Index(
            "ix_bp_org_memberships_org_status",
            "billing_provider_organization_id",
            "status",
        ),
        Index(
            "ix_bp_org_memberships_user_status",
            "user_id",
            "status",
        ),
        Index(
            "uq_bp_org_memberships_active_pair",
            "user_id",
            "billing_provider_organization_id",
            unique=True,
            postgresql_where=text("status = 'ACTIVE'"),
            sqlite_where=text("status = 'ACTIVE'"),
        ),
    )
