from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class Vendor(Base):
    __tablename__ = "vendors"

    __table_args__ = (
        Index("ix_vendors_tenant_status", "tenant_id", "status"),
        Index("ix_vendors_tenant_name", "tenant_id", "name"),
        Index("ix_vendors_tenant_type", "tenant_id", "vendor_type"),
        Index("ix_vendors_tenant_npi", "tenant_id", "npi"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    vendor_type = Column(String(64), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    ncpdp_id = Column(String(32), nullable=True)
    address_street = Column(String(255), nullable=True)
    address_city = Column(String(120), nullable=True)
    address_state = Column(String(32), nullable=True)
    address_zip = Column(String(32), nullable=True)
    phone = Column(String(64), nullable=True)
    fax = Column(String(64), nullable=True)
    email = Column(String(255), nullable=True)
    contact_person = Column(String(255), nullable=True)
    npi = Column(String(32), nullable=True, index=True)
    npi_exp_date = Column(DateTime(timezone=True), nullable=True)
    rx_state_lic = Column(String(128), nullable=True)
    rx_state_lic_exp_date = Column(DateTime(timezone=True), nullable=True)
    bus_lic = Column(String(128), nullable=True)
    bus_lic_exp_date = Column(DateTime(timezone=True), nullable=True)
    insurance = Column(String(128), nullable=True)
    insurance_exp_date = Column(DateTime(timezone=True), nullable=True)
    note = Column(Text, nullable=True)
    status = Column(
        String(32),
        nullable=False,
        default="active",
        server_default=text("'active'"),
        index=True,
    )

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
