from __future__ import annotations

from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Boolean, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Medication(BaseModel):
    __tablename__ = "medications"

    # ---------------------------------------------------------
    # CORE RELATIONSHIP
    # ---------------------------------------------------------
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # MEDICATION DETAILS
    # ---------------------------------------------------------
    medication_name = Column(String(255), nullable=False)

    canonical_name = Column(
        String(255),
        nullable=True,
        index=True,
        doc="Normalized medication name (RxNorm, etc.)",
    )

    dosage = Column(String(128), nullable=False)
    route = Column(String(64), nullable=False)
    frequency = Column(String(64), nullable=False)

    # ---------------------------------------------------------
    # TIMING
    # ---------------------------------------------------------
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    # ---------------------------------------------------------
    # CLINICAL STATE
    # ---------------------------------------------------------
    is_active = Column(
        Boolean,
        nullable=False,
        server_default="true",
    )

    is_prn = Column(
        Boolean,
        nullable=False,
        server_default="false",
        doc="PRN (as needed) medication flag",
    )

    discontinued_at = Column(
        Date,
        nullable=True,
    )

    discontinued_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    discontinue_reason = Column(
        Text,
        nullable=True,
    )

    # ---------------------------------------------------------
    # SIGNATURE / APPROVAL TRACEABILITY
    # ---------------------------------------------------------
    # Links this "current meds list" row to the signed PhysicianOrder that
    # authorized it (set when the medication came from Orders Hub or an
    # Import Pack). NULL means this medication was entered through the
    # legacy quick-add flow with no MD sign-off on file — surfaced in the
    # UI as "No signed order on file" so staff/agency have full visibility
    # into which medications are (or are not) backed by a signed order.
    physician_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("physician_orders.id"),
        nullable=True,
        index=True,
    )

    # ---------------------------------------------------------
    # RELATIONSHIPS
    # ---------------------------------------------------------
    patient = relationship(
        "Patient",
        back_populates="medications",
    )

    # ---------------------------------------------------------
    # INDEXES
    # ---------------------------------------------------------
    __table_args__ = (
        Index(
            "ix_medications_patient_active",
            "patient_id",
            "is_active",
        ),
    )