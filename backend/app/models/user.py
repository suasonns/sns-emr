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

    billing_provider_organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "billing_provider_organizations.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_users_billing_provider_organization_id",
        ),
        nullable=True,
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
        ForeignKey("physicians.id"),
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
