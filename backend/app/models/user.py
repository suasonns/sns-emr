# models/user.py

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index, Text, text
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
