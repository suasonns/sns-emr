from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class FacesheetFieldSuggestion(Base):
    """A proposed PatientFaceSheet field change that was NOT auto-applied.

    Real hospice/billing workflow requires that facesheet fields --
    demographic (name, DOB, gender, address, phone), insurance (MBI,
    payer, policy number, subscriber information), and any future
    OCR/AI-sourced field -- can be legitimately corrected later, e.g. a
    Medicare rejection reveals a name/DOB/MBI mismatch, or an insurance
    card scan surfaces a policy number correction. At the same time, an
    automated document-ingestion pipeline must never silently overwrite
    an already-populated value with OCR noise from an unrelated
    document, and PatientFaceSheet must remain the single source of
    truth (see docs/architecture/InsuranceMappingReconciliation.md and
    docs/workflows/SourceOfTruthMatrix.md).

    This table is the reconciliation point: whenever an ingestion
    pipeline sees a new document's extracted value conflict with an
    existing, non-empty facesheet value, it records the conflict here
    instead of writing it, and a human accepts/rejects/dismisses it via
    the generic field-suggestion review endpoints (app/api/
    field_suggestions.py). This table is a STAGING QUEUE, never itself a
    source of truth -- no consumer (billing, claims, readiness) may read
    from it; only PatientFaceSheet is authoritative once a suggestion is
    accepted and applied.

    Clinical fields (diagnoses, evidence, labs, RNICA findings) are
    entirely unaffected by this table -- they continue to update
    automatically via the separate evidence/harvester pipeline.
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

    # See FACESHEET_SUGGESTIBLE_FIELDS below for the full allowed domain
    # (demographic + insurance fields today; extensible to future
    # OCR/AI-sourced fields without any schema change).
    field_name = Column(String, nullable=False)

    # Stored as text for uniformity across the differently-typed fields
    # this applies to (dates are stored as ISO-8601 strings).
    current_value = Column(String, nullable=True)
    suggested_value = Column(String, nullable=True)

    source_document_id = Column(
        UUID(as_uuid=True), ForeignKey("document_records.id"), nullable=True
    )

    # pending | accepted | rejected | dismissed | auto_applied
    status = Column(String, nullable=False, default="pending")

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    patient = relationship("Patient")


# Generic field-suggestion domain registry: every field_name value this
# framework is allowed to carry, mapped to the PatientFaceSheet attribute
# it reconciles into and its value type (for correct type coercion on
# apply). This is the ONE place new suggestible fields are added --
# demographic, insurance, or future OCR/AI fields alike. Anything not
# listed here is rejected by the review API (app/api/field_suggestions.py)
# to prevent an uncontrolled/unauthorized field from being smuggled
# through the queue.
FACESHEET_SUGGESTIBLE_FIELDS: dict[str, str] = {
    # Demographic (identity + administrative)
    "first_name": "string",
    "last_name": "string",
    "dob": "date",
    "gender": "string",
    "phone": "string",
    "address": "string",
    # Insurance -- see docs/architecture/InsuranceMappingReconciliation.md
    "mbi_number": "string",
    "primary_payer": "string",
    "primary_policy_number": "string",
    "secondary_payer": "string",
    "secondary_policy_number": "string",
    "subscriber_name": "string",
    "subscriber_relationship": "string",
    "subscriber_id": "string",
}
