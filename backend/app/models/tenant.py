from __future__ import annotations

from sqlalchemy import Boolean, Column, String, Index, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class Tenant(BaseModel):
    __tablename__ = "tenants"

    # ---------------------------------------------------------
    # CORE IDENTITY
    # ---------------------------------------------------------

    legal_name = Column(
        String(255),
        nullable=False,
    )

    display_name = Column(
        String(255),
        nullable=False,
    )

    # ---------------------------------------------------------
    # ✅ NPI (CRITICAL — REQUIRED FOR BILLING / EDI)
    # ---------------------------------------------------------

    npi = Column(
        String(10),
        nullable=False,
        index=True,
    )
    # Must be exactly 10 digits (validated below)

    # ---------------------------------------------------------
    # TENANT TYPE (CRITICAL FOR BILLING + UI)
    # ---------------------------------------------------------

    tenant_type = Column(
        String(32),
        nullable=False,
        server_default=text("'DEV'"),
        index=True,
    )

    # ---------------------------------------------------------
    # STATUS CONTROL
    # ---------------------------------------------------------

    status = Column(
        String(32),
        nullable=False,
        server_default=text("'ACTIVE'"),
        index=True,
    )

    ai_enabled = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
        index=True,
    )

    billing_enabled = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
        index=True,
    )

    # ---------------------------------------------------------
    # AUDIT SAFETY
    # ---------------------------------------------------------

    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # ---------------------------------------------------------
    # OPTIONAL (ENTERPRISE READY)
    # ---------------------------------------------------------

    environment_tag = Column(
        String(64),
        nullable=True,
    )

    # ---------------------------------------------------------
    # ENTERPRISE CONSTRAINTS
    # ---------------------------------------------------------

    __table_args__ = (

        # ✅ Enforce valid tenant types
        CheckConstraint(
            "tenant_type IN ('PRODUCTION', 'TRAINING', 'DEV')",
            name="ck_tenant_type_valid",
        ),

        # ✅ Enforce valid status
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')",
            name="ck_tenant_status_valid",
        ),

        # ✅ NPI must be 10 characters
        CheckConstraint(
            "char_length(npi) = 10",
            name="ck_tenant_npi_length",
        ),

        Index(
            "ix_tenants_type_status",
            "tenant_type",
            "status",
        ),
    )