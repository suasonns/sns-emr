from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PatientAllergy(BaseModel):
    """
    Structured, patient-level allergy record.

    Replaces free-text-only allergy capture with a queryable record that the
    medication safety engine can cross-reference against new/active meds.
    """

    __tablename__ = "patient_allergies"

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Raw clinician-entered allergen text (audit-preserving, e.g. "penicillin", "sulfa drugs")
    allergen_text = Column(String(255), nullable=False)

    # DRUG | FOOD | ENVIRONMENTAL | OTHER
    allergen_type = Column(
        String(32),
        nullable=False,
        server_default="DRUG",
    )

    # Canonical drug-class key resolved via allergy_class_map.json (e.g. "PENICILLINS", "NSAIDS")
    # Null when allergen_type != DRUG or no class could be resolved.
    drug_class = Column(String(64), nullable=True, index=True)

    reaction_description = Column(Text, nullable=True)

    # MILD | MODERATE | SEVERE | ANAPHYLAXIS
    severity = Column(String(32), nullable=True)

    active = Column(Boolean, nullable=False, server_default="true")

    patient = relationship(
        "Patient",
        back_populates="allergies",
    )

    __table_args__ = (
        Index("ix_patient_allergies_patient_active", "patient_id", "active"),
    )
