from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class Physician(Base):
    __tablename__ = "physicians"

    __table_args__ = (
        Index("ix_physicians_tenant_status", "tenant_id", "status"),
        Index("ix_physicians_tenant_display_name", "tenant_id", "display_name"),
        Index("ix_physicians_tenant_npi", "tenant_id", "npi"),
        # Required by tenants.default_medical_director_physician_id's
        # composite FK (see tenant.py), which references
        # (physicians.tenant_id, physicians.id) -- Postgres requires a
        # unique constraint/index on the referenced columns. This was
        # already present in the database (every migration since its
        # introduction created it), but was never declared on this model,
        # so `alembic revision --autogenerate` treated it as drift to be
        # dropped. Declaring it here instead of dropping it keeps the FK
        # target valid and makes the model match the database.
        UniqueConstraint("tenant_id", "id", name="uq_physicians_tenant_id_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    npi = Column(String(32), nullable=True, index=True)
    first_name = Column(String(120), nullable=True)
    last_name = Column(String(120), nullable=True)
    display_name = Column(String(255), nullable=False, index=True)
    title = Column(String(32), nullable=True)
    specialty_type = Column(String(255), nullable=True)
    license_number = Column(String(128), nullable=True)
    taxonomy_code = Column(String(64), nullable=True)
    address_street = Column(String(255), nullable=True)
    address_suite = Column(String(128), nullable=True)
    address_city = Column(String(120), nullable=True)
    address_state = Column(String(32), nullable=True)
    address_zip = Column(String(32), nullable=True)
    phone = Column(String(64), nullable=True)
    fax = Column(String(64), nullable=True)
    email = Column(String(255), nullable=True)
    contact_name = Column(String(255), nullable=True)
    protocol_notes = Column(Text, nullable=True)
    status = Column(
        String(32),
        nullable=False,
        default="active",
        server_default=text("'active'"),
        index=True,
    )
    register_for_eprescription = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    pecos_status = Column(String(32), nullable=True)
    pecos_checked_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )


class PhysicianPecosCache(Base):
    __tablename__ = "physician_pecos_cache"

    __table_args__ = (
        Index("ix_physician_pecos_cache_npi", "npi", unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    npi = Column(String(32), nullable=False, unique=True)
    status = Column(String(32), nullable=False)
    source = Column(String(128), nullable=True)
    reason = Column(Text, nullable=True)
    checked_at = Column(DateTime(timezone=True), nullable=True)
    refreshed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
