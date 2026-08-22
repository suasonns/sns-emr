from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Index, String, UniqueConstraint
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
    party, DPOA, healthcare agent, decision maker, or emergency contact
    is.

    Design:
        - One row per (patient_id, role). Updated in place - like
          PatientPhysicianAssignment, not an append-only audit history
          like PatientCodeStatus, since the ticket only asks for one
          shared current record per role, not a legal audit trail.
    """

    __tablename__ = "patient_contacts"

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
    # DECISION_MAKER | EMERGENCY_CONTACT
    role = Column(String(64), nullable=False)

    name = Column(String(255), nullable=True)
    relationship_to_patient = Column(String(120), nullable=True)
    phone = Column(String(64), nullable=True)
    address = Column(String(255), nullable=True)

    # Source workflow/document that set this value, e.g. FACESHEET, RNICA,
    # ACP, CONSENT.
    source = Column(String(64), nullable=False, server_default="FACESHEET")

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
