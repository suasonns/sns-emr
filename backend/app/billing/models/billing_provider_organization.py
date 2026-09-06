from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel

BILLING_PROVIDER_ORGANIZATION_STATUSES = {"ACTIVE", "INACTIVE"}


class BillingProviderOrganization(BaseModel):
    __tablename__ = "billing_provider_organizations"

    name = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    organization_type = Column(
        String(64),
        nullable=False,
        index=True,
    )

    status = Column(
        String(32),
        nullable=False,
        server_default=text("'ACTIVE'"),
        index=True,
    )

    notes = Column(Text, nullable=True)

    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_billing_provider_organization_status_valid",
        ),
        Index("ix_billing_provider_org_type_status", "organization_type", "status"),
    )
