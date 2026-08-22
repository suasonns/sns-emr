from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel


class PatientCodeStatus(BaseModel):
    """
    Authoritative, audited code-status record.

    Replaces facesheet-only free text with a single shared, auditable
    record so Facesheet, RNICA, ACP/consent, Care Overview, and Orders can
    never disagree about a patient's resuscitation status.

    Design:
        - Every change is a NEW row. Rows are never overwritten in place.
        - Exactly one row per patient has is_current = true at any time;
          all prior rows become is_current = false and are preserved
          forever as the audit trail (e.g. Full Code -> DNR -> Comfort
          Measures Only, each with its own effective_date/source/notes).
        - created_by / created_at (from BaseModel) record who set this row
          and when it was recorded.
    """

    __tablename__ = "patient_code_statuses"

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # FULL_CODE | DNR | DNI | COMFORT_MEASURES_ONLY | OTHER
    code_status = Column(String(64), nullable=False)

    effective_date = Column(Date, nullable=False, server_default=func.current_date())

    # Source workflow/document that set this value, e.g. INTAKE, RN_ICA,
    # POLST, PHYSICIAN_ORDER, FACESHEET, ACP.
    source = Column(String(64), nullable=False, server_default="FACESHEET")

    notes = Column(Text, nullable=True)

    is_current = Column(Boolean, nullable=False, server_default="true")

    patient = relationship("Patient", back_populates="code_statuses")

    __table_args__ = (
        Index("ix_patient_code_statuses_patient_current", "patient_id", "is_current"),
        Index("ix_patient_code_statuses_patient_effective", "patient_id", "effective_date"),
    )
