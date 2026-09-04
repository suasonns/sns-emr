from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class FacesheetFieldSuggestion(Base):
    """A proposed demographic-field change that was NOT auto-applied.

    Real hospice/billing workflow requires that identity and
    administrative facesheet fields (name, DOB, MRN, gender, address,
    phone) can be legitimately corrected later -- e.g. a Medicare
    rejection reveals a name/DOB/MBI mismatch that must be fixed. At the
    same time, an automated document-ingestion pipeline must never
    silently overwrite an already-populated demographic value with OCR
    noise from an unrelated document.

    This table is the reconciliation point: whenever
    persist_patient_from_hnp_extraction() sees a new document's
    extracted value conflict with an existing, non-empty demographic
    value, it records the conflict here instead of writing it, and a
    human accepts/rejects/dismisses it via the facesheet suggestions
    endpoints. Clinical fields (diagnoses, evidence, labs, RNICA
    findings) are entirely unaffected by this table -- they continue to
    update automatically via the separate evidence/harvester pipeline.
    """

    __tablename__ = "facesheet_field_suggestions"

    __table_args__ = (
        Index(
            "ix_facesheet_field_suggestions_patient_status",
            "tenant_id",
            "patient_id",
            "status",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)

    # One of: first_name, last_name, dob, mrn, gender, address, phone.
    field_name = Column(String, nullable=False)

    # Stored as text for uniformity across the differently-typed fields
    # this applies to (dates are stored as ISO-8601 strings).
    current_value = Column(String, nullable=True)
    suggested_value = Column(String, nullable=True)

    source_document_id = Column(
        UUID(as_uuid=True), ForeignKey("document_records.id"), nullable=True
    )

    # pending | accepted | rejected | dismissed
    status = Column(String, nullable=False, default="pending")

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    patient = relationship("Patient")
