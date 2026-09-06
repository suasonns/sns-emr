from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class PatientContactSuggestion(Base):
    """A proposed PatientContact field change that was NOT auto-applied.

    Mirrors app.models.facesheet_field_suggestion.FacesheetFieldSuggestion,
    but scoped to shared caregiver/decision-maker contact roles
    (PatientContact) rather than facesheet demographic fields -- the two
    are separate domains with separate reconciliation rules (contacts
    honor PatientContact.manual_override; demographics honor
    Tenant.facesheet_protection_mode), so they are NOT merged into one
    generic table.

    Whenever app.services.contact_harvest_service sees a document-derived
    contact value conflict with an existing, non-empty PatientContact
    field -- or the field was ever manually overridden -- it records the
    conflict here instead of writing it, and a human accepts/rejects/
    dismisses it via the patient contact-suggestions endpoints.
    """

    __tablename__ = "patient_contact_suggestions"

    __table_args__ = (
        Index(
            "ix_patient_contact_suggestions_patient_status",
            "tenant_id",
            "patient_id",
            "status",
        ),
        Index(
            "ix_patient_contact_suggestions_patient_role",
            "patient_id",
            "role",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)

    # PRIMARY_CAREGIVER | RESPONSIBLE_PARTY | DPOA | HEALTHCARE_AGENT |
    # DECISION_MAKER | EMERGENCY_CONTACT | GUARDIAN | CONSERVATOR
    role = Column(String(64), nullable=False)

    # One of: name, relationship_to_patient, phone, email, address.
    field_name = Column(String(64), nullable=False)

    current_value = Column(String, nullable=True)
    suggested_value = Column(String, nullable=True)

    source_document_id = Column(
        UUID(as_uuid=True), ForeignKey("document_records.id"), nullable=True
    )
    source_document_name = Column(String(255), nullable=True)
    source_document_page = Column(Integer, nullable=True)
    extractor_version = Column(String(64), nullable=True)
    extraction_timestamp = Column(DateTime(timezone=True), nullable=True)

    # pending | accepted | rejected | dismissed
    status = Column(String, nullable=False, default="pending")

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    patient = relationship("Patient")
