# models/tenant.py

from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKeyConstraint, String, Index, CheckConstraint, text
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
    # FACESHEET DEMOGRAPHIC PROTECTION
    # ---------------------------------------------------------
    # Controls how persist_patient_from_hnp_extraction() reacts when an
    # uploaded document's extracted demographic value (name/dob/mrn/
    # gender/address/phone) conflicts with an already-populated facesheet
    # value:
    #   OFF            -- overwrite automatically (legacy behavior).
    #   WARN            -- overwrite automatically, but record an audited
    #                       FacesheetFieldSuggestion for visibility.
    #   REQUIRE_REVIEW  -- never overwrite; queue a pending suggestion for
    #                       a human to accept/reject (default).
    facesheet_protection_mode = Column(
        String(32),
        nullable=False,
        server_default=text("'REQUIRE_REVIEW'"),
    )

    # ---------------------------------------------------------
    # AGENCY-OWNED OPERATIONAL DEFAULTS
    # ---------------------------------------------------------
    # The hospice Medical Director is an agency governance decision, never
    # something hospital documents determine. This FK points at a record in
    # this SAME tenant's own Physician directory (physicians.tenant_id must
    # match) -- never another tenant's physician, never a platform/seed
    # record. Nullable: an agency that has not configured a default sees
    # NOT_CONFIGURED, never a fallback to some other tenant's data or a
    # development seed value. A per-patient Facesheet override always takes
    # precedence over this tenant default (see _apply_tenant_default_
    # medical_director in app/api/patients.py, which only fills a *blank*
    # medical_director_name -- it never overwrites an existing value).
    default_medical_director_physician_id = Column(
        UUID(as_uuid=True),
        nullable=True,
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
        CheckConstraint(
            "facesheet_protection_mode IN ('OFF', 'WARN', 'REQUIRE_REVIEW')",
            name="ck_tenant_facesheet_protection_mode_valid",
        ),
        # Composite FK: a single-column FK on physicians.id alone cannot
        # stop this tenant's default from pointing at ANOTHER tenant's
        # physician row. Matching against (tenant_id, id) on physicians
        # (see uq_physicians_tenant_id_id) enforces tenant isolation at
        # the database level, not just in application code.
        ForeignKeyConstraint(
            ["id", "default_medical_director_physician_id"],
            ["physicians.tenant_id", "physicians.id"],
            name="fk_tenants_default_medical_director_physician_id",
            ondelete="SET NULL",
            use_alter=True,
        ),
        Index(
            "ix_tenants_type_status",
            "tenant_type",
            "status",
        ),
    )