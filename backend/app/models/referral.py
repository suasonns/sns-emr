# models/referral.py

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base


class Referral(Base):
    """Incoming referral intake awaiting staff review.

    A referral is created directly from the intake form (hospital/SNF/
    physician send-in) and starts life as PENDING with no Patient record
    yet. Staff either ACCEPT it (which converts it into a full Patient +
    PatientFaceSheet + PatientDiagnosis + Admission, mirroring the prior
    direct-create behavior) or DECLINE it (with a required reason), leaving
    a permanent audit trail either way.
    """

    __tablename__ = "referrals"

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "PENDING")
        super().__init__(**kwargs)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status = Column(String(32), nullable=False, server_default=text("'PENDING'"), index=True)

    # ---------------------------------------------------------
    # Patient information captured at intake
    # ---------------------------------------------------------
    first_name = Column(String(128), nullable=False)
    middle_name = Column(String(128), nullable=True)
    last_name = Column(String(128), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    phone = Column(String(32), nullable=True)
    address = Column(String(255), nullable=True)
    city = Column(String(128), nullable=True)
    state = Column(String(64), nullable=True)
    zip = Column(String(16), nullable=True)
    gender = Column(String(32), nullable=True)
    language = Column(String(64), nullable=True)
    religion = Column(String(64), nullable=True)
    marital_status = Column(String(64), nullable=True)

    # ---------------------------------------------------------
    # Payer
    # ---------------------------------------------------------
    primary_payer = Column(String(128), nullable=True)
    primary_policy_number = Column(String(128), nullable=True)
    authorization_status = Column(String(64), nullable=True)

    # ---------------------------------------------------------
    # Referral & clinical
    # ---------------------------------------------------------
    current_level_of_care = Column(String(64), nullable=True)
    primary_diagnosis = Column(String(255), nullable=True)
    secondary_diagnoses = Column(Text, nullable=True)
    attending_physician_name = Column(String(255), nullable=True)
    attending_physician_npi = Column(String(32), nullable=True)
    referral_source = Column(String(255), nullable=True)
    referral_date = Column(Date, nullable=True)
    special_instructions = Column(Text, nullable=True)

    # ---------------------------------------------------------
    # Responsible party / emergency contact
    # ---------------------------------------------------------
    responsible_party_name = Column(String(255), nullable=True)
    responsible_party_relationship = Column(String(128), nullable=True)
    responsible_party_phone = Column(String(32), nullable=True)
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_relationship = Column(String(128), nullable=True)
    emergency_contact_phone = Column(String(32), nullable=True)

    # ---------------------------------------------------------
    # Review / decision audit trail
    # ---------------------------------------------------------
    decline_reason = Column(Text, nullable=True)
    converted_patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
