from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PatientContact(BaseModel):
    """
    Authoritative, shared contact/decision-maker record for a patient.

    Replaces facesheet-only free text (responsible_party_*,
    emergency_contact_*) and RNICA-only free text (demographics.pcg.*,
    advancedCarePlanning.decisionMaker/poaName/poaPhone) with a single
    shared record per (patient, role) so Facesheet, RNICA, ACP, and
    Consents never disagree about who the primary caregiver, responsible
    party, DPOA, healthcare agent, decision maker, guardian, conservator,
    or emergency contact is.

    Design:
        - One row per (patient_id, role). Updated in place - like
          PatientPhysicianAssignment, not an append-only audit history
          like PatientCodeStatus, since the ticket only asks for one
          shared current record per role, not a legal audit trail.
        - Source attribution (attribution_source/source_document_*/
          extractor_version) mirrors the maturity bar set by
          PatientDiagnosis/Certification/BenefitPeriod: every value must
          be traceable to where it came from and whether a human
          overrode it. A conflicting document-harvested value is never
          silently applied over an existing value -- see
          app.services.contact_harvest_service, which queues a
          PatientContactSuggestion for review instead.
    """

    __tablename__ = "patient_contacts"

    # Overrides BaseModel.created_by: this table's migration
    # (a1c2d3e4f5b6_add_patient_contacts) created a real FK constraint but
    # no separate index on created_by, unlike the BaseModel default.
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

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

    # PRIMARY_CAREGIVER | RESPONSIBLE_PARTY | DPOA | HEALTHCARE_AGENT |
    # DECISION_MAKER | EMERGENCY_CONTACT | GUARDIAN | CONSERVATOR
    role = Column(String(64), nullable=False)

    name = Column(String(255), nullable=True)
    relationship_to_patient = Column(String(120), nullable=True)
    phone = Column(String(64), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)

    # Whether this role is the patient's preferred contact for
    # communication/outreach when more than one role is populated.
    is_preferred = Column(Boolean, nullable=False, server_default="false")

    # Source workflow/module that set this value, e.g. FACESHEET, RNICA,
    # ACP, CONSENT, DOCUMENT_HARVEST.
    source = Column(String(64), nullable=False, server_default="FACESHEET")

    # ---------------------------------------------------------
    # SOURCE ATTRIBUTION (production parity with PatientDiagnosis /
    # Certification / BenefitPeriod)
    # ---------------------------------------------------------

    # HARVESTED | MANUAL | CALCULATED | IMPORTED
    attribution_source = Column(
        String(32),
        nullable=False,
        server_default="MANUAL",
    )

    source_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_records.id"),
        nullable=True,
    )
    source_document_name = Column(String(255), nullable=True)
    source_document_page = Column(Integer, nullable=True)
    extraction_timestamp = Column(DateTime(timezone=True), nullable=True)
    extractor_version = Column(String(64), nullable=True)

    # Set the first time a human explicitly saves this role through the
    # manual contact-entry endpoint. Once true, a later conflicting
    # document-harvested value is ALWAYS queued for review (never
    # auto-applied), regardless of tenant facesheet_protection_mode.
    manual_override = Column(Boolean, nullable=False, server_default="false")
    manual_override_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    manual_override_at = Column(DateTime(timezone=True), nullable=True)

    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    patient = relationship("Patient", back_populates="contacts")

    __table_args__ = (
        UniqueConstraint("patient_id", "role", name="uq_patient_contact_role"),
        Index("ix_patient_contacts_patient_role", "patient_id", "role"),
    )
