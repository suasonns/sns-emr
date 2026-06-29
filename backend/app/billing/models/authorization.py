from __future__ import annotations

import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Authorization(Base):
    __tablename__ = "authorization_records"

    # ---------------------------------------------------------
    # PRIMARY KEY
    # ---------------------------------------------------------
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ---------------------------------------------------------
    # TENANT
    # ---------------------------------------------------------
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # PATIENT
    # ---------------------------------------------------------
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # AUTHORIZATION DATA
    # ---------------------------------------------------------
    authorization_number = Column(String(100), nullable=True)

    service_type = Column(
        String(50),
        nullable=True,
        doc="RN / HHA / PT / OT / ST / MSW",
    )

    status = Column(
        String(32),
        nullable=False,
        default="PENDING",
        doc="PENDING / APPROVED / DENIED / EXPIRED",
    )

    # ---------------------------------------------------------
    # AUDIT
    # ---------------------------------------------------------
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    created_by = Column(String(255), nullable=True)

    # ---------------------------------------------------------
    # RELATIONSHIPS
    # ---------------------------------------------------------
    patient = relationship("Patient")
    tenant = relationship("Tenant")

    # ---------------------------------------------------------
    # INDEXES
    # ---------------------------------------------------------
    __table_args__ = (
        Index("ix_authorization_patient", "patient_id"),
    )