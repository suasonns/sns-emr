from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

FACILITY_AUDIT_ENTITY_TYPES = {"EXPECTATION", "ALLOCATION", "ALERT"}


class FacilityPaymentAuditLog(Base):
    __tablename__ = "facility_payment_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_type = Column(String(32), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    field_name = Column(String(128), nullable=False)
    previous_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    role = Column(String(64), nullable=True)
    reason = Column(Text, nullable=True)
    supporting_reference = Column(Text, nullable=True)
    correlation_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    tenant = relationship("Tenant")
    user = relationship("User")

    __table_args__ = (
        Index("ix_facility_payment_audit_tenant_entity", "tenant_id", "entity_type", "entity_id"),
    )
