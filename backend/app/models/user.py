# models/user.py

from sqlalchemy import Column, String, Boolean, Date, DateTime, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel
from app.models.tenant import Tenant  # ensures table registration


class User(BaseModel):
    __tablename__ = "users"

    # =========================================================
    # TENANT ISOLATION (CRITICAL)
    # =========================================================
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # =========================================================
    # IDENTITY
    # =========================================================
    email = Column(
        String,
        nullable=False,
    )

    password_hash = Column(
        String(255),
        # Null until a password is set; login rejects users without a hash.
        nullable=True,
    )

    full_name = Column(
        String,
        nullable=False,
    )

    first_name = Column(
        String(100),
        nullable=True,
    )

    middle_name = Column(
        String(100),
        nullable=True,
    )

    last_name = Column(
        String(100),
        nullable=True,
    )

    display_name = Column(
        String(200),
        nullable=True,
    )

    # =========================================================
    # ROLE (FUNCTIONAL ROLE)
    # =========================================================
    role = Column(
        String,
        nullable=False,
        index=True,
    )

    # =========================================================
    # LICENSE (FOR CLINICAL STAFF)
    # =========================================================
    license_number = Column(
        String,
        nullable=True,
    )

    # =========================================================
    # ACCESS CONTROL (NEW - PRODUCTION CRITICAL)
    # =========================================================
    access_level = Column(
        String(32),
        nullable=False,
        server_default=text("'ROLE_BASED'"),
        index=True,
    )

    # =========================================================
    # STATUS
    # =========================================================
    active = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
        index=True,
    )

    # =========================================================
    # STAFF PROFILE (HR — Insights > HR)
    # Deliberately excludes SSN (needs an encryption-at-rest plan),
    # pay rate, and license/document expiration tracking.
    # =========================================================
    date_of_birth = Column(Date, nullable=True)
    address_street = Column(String(255), nullable=True)
    address_city = Column(String(100), nullable=True)
    address_state = Column(String(2), nullable=True)
    address_zip = Column(String(10), nullable=True)
    phone = Column(String(20), nullable=True)
    home_phone = Column(String(20), nullable=True)

    job_title = Column(String(150), nullable=True)
    discipline = Column(String(50), nullable=True)
    npi = Column(String(10), nullable=True)
    employment_date = Column(Date, nullable=True)
    employment_end_date = Column(Date, nullable=True)

    # C=Clinical, A=Administrative, X=Contracted Staff, Y=Referral Source
    staff_type = Column(String(1), nullable=True)

    # =========================================================
    # SNS STAFF & ACCESS (Phase UM-2, platform-owner staff only)
    # Department is presentational/organizational only -- see
    # app/core/departments.py; it never grants permissions. `notes` is a
    # free-text admin note. `updated_by` complements the existing
    # `created_by` (BaseModel) for the same "who touched this record" audit
    # trail, since BaseModel only tracks creation, not edits.
    # =========================================================
    department = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    # Distinguishes human platform staff from non-human platform identities
    # (service/automation accounts, API clients) -- see
    # app/core/account_types.py. Defaults to HUMAN_STAFF for every account
    # created through the existing staff workflow.
    account_type = Column(String(32), nullable=False, server_default="HUMAN_STAFF")

    # Platform-identity accountability (Service Account / Automation
    # Account / API Client only -- never presented as ordinary employee
    # fields). `responsible_owner_id` is the SNS human staff member
    # accountable for this identity; `identity_purpose` is why it exists;
    # `identity_scope` is what it is authorized to touch (API Clients).
    responsible_owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    identity_purpose = Column(Text, nullable=True)
    identity_scope = Column(String(255), nullable=True)

    # SNS Platform assignment (highest organizational assignment level,
    # above Department/Job Title/Platform Role/Access Level -- see the
    # approved SNS Staff & Access organizational hierarchy). Only SNS
    # Hospice Solutions exists today; this column exists so future SNS
    # platforms (e.g. SNS Home Health Solutions, SNS Scribe) can be added
    # later without a User Management redesign. See
    # app/core/platforms.py for the canonical allowed-values list.
    platform = Column(String(120), nullable=False, server_default="SNS Hospice Solutions")

    # Distinct SNS platform-staff lifecycle status (ACTIVE / SUSPENDED /
    # DISABLED / REMOVED -- see app.core.roles.PLATFORM_STAFF_STATUSES).
    # Deliberately separate from `active` above: `active` remains the one
    # global auth gate every login/refresh check relies on for every user
    # type; this column exists only to distinguish *why* an SNS platform
    # staff account is (or isn't) active without overloading that boolean
    # with app-wide semantics. Kept in sync by the API layer (ACTIVE syncs
    # active=true; SUSPENDED/DISABLED/REMOVED sync active=false).
    platform_staff_status = Column(
        String(32),
        nullable=False,
        server_default=text("'ACTIVE'"),
    )

    # Forces the frontend to block access with a mandatory password-change
    # screen until the user sets their own password. Set true whenever an
    # admin issues/resets a temporary password (see app/api/staff.py);
    # cleared by /auth/change-password.
    must_change_password = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    # Single-use, expiring token backing the "set/reset password via link"
    # flow. We store only a SHA-256 hash of the token (never the raw value),
    # same principle as password_hash. Cleared once used or on password
    # change. Ready to be emailed once email sending is wired up.
    password_reset_token_hash = Column(String(64), nullable=True)
    password_reset_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Encrypted at rest (Fernet, see app/core/crypto.py). ssn_last4 is
    # plaintext by design (industry-standard masked display, e.g. card
    # last4) so the roster can show "***-**-1234" without decrypting.
    # The full value is only decrypted via the admin-gated, audit-logged
    # reveal endpoint.
    ssn_encrypted = Column(Text, nullable=True)
    ssn_last4 = Column(String(4), nullable=True)

    # Deterministic HMAC-SHA256 of the normalized SSN (see
    # app/core/crypto.ssn_lookup_hash). Fernet ciphertext is randomized per
    # encryption, so it can never be compared across rows; this hash lets us
    # find other User rows (any tenant, any email/password) that belong to
    # the same physical person, to power the cross-agency account linking
    # shown after login ("agencies you're also connected to").
    ssn_lookup_hash = Column(String(64), nullable=True, index=True)

    # =========================================================
    # PHYSICIAN IDENTITY LINKAGE (owner directive 2026-08-21)
    #
    # Identity VERIFICATION, not a visibility model by itself. A role label
    # (MEDICAL_DIRECTOR/ATTENDING_PHYSICIAN/HOSPICE_PHYSICIAN/NP/PA) never
    # by itself proves which directory Physician, patient assignments, or
    # signature obligations belong to this account. Fail-closed: until an
    # authorized administrator links+verifies physician_id, a provider-role
    # account gets ZERO patient/order visibility and ZERO signing capability
    # — never an agency-wide fallback. See
    # app/services/physician_identity_service.py for enforcement.
    # =========================================================
    physician_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "physicians.id",
            name="fk_users_physician_id_physicians",
            use_alter=True,
        ),
        nullable=True,
        index=True,
    )

    # UNLINKED | PENDING_VERIFICATION | ACTIVE | SUSPENDED | ENDED
    physician_link_status = Column(
        String(32),
        nullable=False,
        server_default=text("'UNLINKED'"),
        index=True,
    )

    physician_linked_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    physician_linked_at = Column(DateTime(timezone=True), nullable=True)
    physician_linkage_verified_at = Column(DateTime(timezone=True), nullable=True)
    physician_linkage_reason = Column(Text, nullable=True)

    physician_unlinked_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    physician_unlinked_at = Column(DateTime(timezone=True), nullable=True)
    physician_unlink_reason = Column(Text, nullable=True)

    # =========================================================
    # CONSTRAINTS (ENTERPRISE SAFE)
    # =========================================================
    __table_args__ = (
        Index(
            "uq_users_tenant_email",
            "tenant_id",
            "email",
            unique=True,
        ),
    )
