# models/user.py

from sqlalchemy import Column, String, Boolean, ForeignKey, Index, text
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
