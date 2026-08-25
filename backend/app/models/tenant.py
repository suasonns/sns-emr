# models/tenant.py

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
    # OPERATING AUTHORITY (REQUIRED TO BILL MEDICARE)
    # ---------------------------------------------------------

    ein = Column(
        String(10),
        nullable=True,
        index=True,
    )
    # Employer Identification Number, 9 digits, stored unformatted.

    ptan = Column(
        String(32),
        nullable=True,
        index=True,
    )
    # Provider Transaction Access Number / CMS Certification Number.

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
    # ✅ CBSA CODE (REQUIRED FOR REAL CMS WAGE-INDEX RATE LOOKUPS)
    # ---------------------------------------------------------
    # Core Based Statistical Area code for the tenant's primary service
    # location, per the CMS hospice wage index tables. Used to look up the
    # real, published wage index for computing wage-adjusted per-diem rates.
    # Nullable: agencies without this configured fall back to $0.00 rates
    # (safer than guessing) rather than an invented default.
    cbsa_code = Column(
        String(10),
        nullable=True,
    )

    # ---------------------------------------------------------
    # ENTERPRISE CONSTRAINTS
    # ---------------------------------------------------------

    __table_args__ = (

        # ✅ Enforce valid tenant types
        # PLATFORM = SNS Hospice Solutions (vendor/platform org: OWNER-role
        # staff — executives, compliance, QA, support, developers,
        # implementation). BILLING = SNS Billing Services (separate billing
        # org: BILLING-role staff). Both are real, permanent organizations,
        # not hospice agencies — kept distinct so tenant_id stays required
        # (no nullable tenant_id) while access is still tenant + domain +
        # role scoped.
        CheckConstraint(
            "tenant_type IN ('PRODUCTION', 'TRAINING', 'DEV', 'PLATFORM', 'BILLING')",
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
        # A start-up agency can be onboarded without Medicare credentials, but
        # it cannot bill until an EIN and PTAN are on file.
        CheckConstraint(
            "billing_enabled = false "
            "OR (ein IS NOT NULL AND ptan IS NOT NULL)",
            name="ck_tenant_billing_requires_operating_authority",
        ),

        CheckConstraint(
            "ein IS NULL OR char_length(ein) = 9",
            name="ck_tenant_ein_length",
        ),
        Index(
            "ix_tenants_type_status",
            "tenant_type",
            "status",
        ),
    )