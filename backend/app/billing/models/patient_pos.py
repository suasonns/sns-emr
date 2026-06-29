from __future__ import annotations

import uuid

from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class PatientPOS(Base):
    __tablename__ = "patient_pos"

    # ---------------------------------------------------------
    # PRIMARY KEY
    # ---------------------------------------------------------
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ---------------------------------------------------------
    # TENANT ISOLATION
    # ---------------------------------------------------------
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # PATIENT LINK
    # ---------------------------------------------------------
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # POS DATA
    # ---------------------------------------------------------
    pos_type = Column(
        String(50),
        nullable=False,
        doc="HOME / SNF / HOSPITAL / ALF / BOARD_AND_CARE",
    )

    facility_name = Column(String(255), nullable=True)

    status = Column(
        String(32),
        nullable=False,
        default="ACTIVE",
        doc="ACTIVE / DISCHARGED / TRANSFERRED",
    )

    effective_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=True, index=True)

    # ---------------------------------------------------------
    # AUDIT FIELDS (CRITICAL)
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
    # CONSTRAINTS + INDEXES
    # ---------------------------------------------------------
    __table_args__ = (
        # ✅ enforce valid date range
        CheckConstraint(
            "end_date IS NULL OR end_date >= effective_date",
            name="ck_patient_pos_dates",
        ),

        # ✅ indexes for performance
        Index(
            "ix_patient_pos_patient_date",
            "patient_id",
            "effective_date",
        ),
        Index(
            "ix_patient_pos_tenant",
            "tenant_id",
        ),
    )