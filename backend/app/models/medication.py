from __future__ import annotations

from sqlalchemy import Column, String, Date, ForeignKey, Boolean, Index
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