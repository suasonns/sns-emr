from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PatientPhysicianAssignment(BaseModel):
    """
    Authoritative, shared physician-role record for a patient.

    Replaces facesheet-only free text (attending_physician_*,
    medical_director_*, associate_medical_director_*) with a single shared
    record per (patient, role) so Facesheet, RNICA, CTI, Orders, and Care
    Overview never disagree about who is Attending, Medical Director, or
    Associate Medical Director.

    Design:
        - One row per (patient_id, role). Updated in place (not append-only
          history like PatientCodeStatus) since the ticket only asks for a
          single shared current record, not a legal audit trail.
        - physician_id optionally links to the tenant physician directory
          (app.models.physician.Physician); free-text fields are kept as a
          fallback for physicians not yet registered in that directory.
        - will_follow_in_hospice only applies to the ATTENDING role.
    """

    __tablename__ = "patient_physician_assignments"

    # Overrides BaseModel.created_by: this table's migration
    # (f3b8c9d0e1a2_add_patient_physician_assignments) created a real FK
    # constraint but no separate index on created_by, unlike the BaseModel
    # default.
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

    # ATTENDING | MEDICAL_DIRECTOR | ASSOCIATE_MEDICAL_DIRECTOR
    role = Column(String(64), nullable=False)

    physician_id = Column(
        UUID(as_uuid=True),
        ForeignKey("physicians.id"),
        nullable=True,
    )

    name = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    phone = Column(String(64), nullable=True)
    fax = Column(String(64), nullable=True)
    npi = Column(String(32), nullable=True)

    will_follow_in_hospice = Column(Boolean, nullable=True)

    # Source workflow/document that set this value, e.g. FACESHEET, RNICA,
    # ADMISSION.
    source = Column(String(64), nullable=False, server_default="FACESHEET")

    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    patient = relationship("Patient", back_populates="physician_assignments")

    __table_args__ = (
        UniqueConstraint("patient_id", "role", name="uq_patient_physician_role"),
        Index("ix_patient_physician_assignments_patient_role", "patient_id", "role"),
    )
