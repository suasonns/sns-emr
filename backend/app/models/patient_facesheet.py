from __future__ import annotations

import uuid
from datetime import datetime, date

from sqlalchemy import (
    Column,
    String,
    Date,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class PatientFaceSheet(Base):
    __tablename__ = "patient_facesheet"
    
    __table_args__ = (
        Index(
            "ix_patient_facesheet_patient_id",
            "patient_id",
        ),
    )

    # --------------------------------------------------
    # ✅ PRIMARY KEY
    # --------------------------------------------------
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # --------------------------------------------------
    # ✅ RELATIONSHIP
    # --------------------------------------------------
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)

    patient = relationship("Patient", back_populates="facesheets")

    # --------------------------------------------------
    # ✅ PERSONAL INFORMATION
    # --------------------------------------------------
    first_name = Column(String)
    middle_name = Column(String)
    last_name = Column(String)
    ssn = Column(String)
    address = Column(String)
    city = Column(String)
    state = Column(String)
    zip = Column(String)
    phone = Column(String)
    dob = Column(Date)
    gender = Column(String)
    race = Column(String)
    ethnicity = Column(String)
    language = Column(String)
    religion = Column(String)
    marital_status = Column(String)

    # --------------------------------------------------
    # ✅ INSURANCE
    # --------------------------------------------------
    primary_payer = Column(String)
    primary_policy_number = Column(String)

    mbi_number = Column(String)

    secondary_payer = Column(String)
    secondary_policy_number = Column(String)
    
    # --------------------------------------------------
    # ✅ AUTHORIZATION
    # --------------------------------------------------

    requires_prior_authorization = Column(Boolean)

    authorization_required_for = Column(String)

    authorization_number = Column(String)

    authorization_status = Column(String)

    authorization_start_date = Column(Date)

    authorization_end_date = Column(Date)
    
    # --------------------------------------------------
    # ✅ CLINICAL
    # --------------------------------------------------
    primary_diagnosis = Column(String)
    secondary_diagnoses = Column(Text)
    allergies = Column(Text)
    
    # --------------------------------------------------
    # ✅ LEVEL OF CARE
    # --------------------------------------------------
    current_level_of_care = Column(String)

    loc_effective_date = Column(Date)
    # --------------------------------------------------
    # ✅ SERVICE DATES
    # --------------------------------------------------
    soc_date = Column(Date)
    ref_date = Column(Date)
    recert_date = Column(Date)
    
    # --------------------------------------------------
    # ✅ ALLERGY
    # --------------------------------------------------
    has_allergies = Column(Boolean)
    
    # --------------------------------------------------
    # ✅ PLACE OF SERVICE
    # --------------------------------------------------
    current_pos_type = Column(String)

    current_pos_name = Column(String)

    current_pos_address = Column(String)

    room_number = Column(String)

    pos_start_date = Column(Date)

    pos_end_date = Column(Date)

    # --------------------------------------------------
    # ✅ CONTACT
    # --------------------------------------------------
    responsible_party_name = Column(String)

    responsible_party_relationship = Column(String)

    responsible_party_phone = Column(String)

    emergency_contact_name = Column(String)

    emergency_contact_relationship = Column(String)

    emergency_contact_phone = Column(String)

    # --------------------------------------------------
    # ✅ PHYSICIAN
    # --------------------------------------------------
    attending_physician_name = Column(String)

    attending_physician_npi = Column(String)

    attending_physician_following = Column(Boolean)

    medical_director_name = Column(String)

    medical_director_npi = Column(String)

    medical_director_designee_name = Column(String)

    medical_director_designee_npi = Column(String)

    associate_medical_director_name = Column(String)

    associate_medical_director_npi = Column(String)

    # --------------------------------------------------
    # ✅ VENDORS
    # --------------------------------------------------
    pharmacy_name = Column(String)

    pharmacy_phone = Column(String)

    pharmacy_fax = Column(String)
    
    dme_vendor_name = Column(String)

    dme_vendor_phone = Column(String)

    # --------------------------------------------------
    # ✅ MORTUARY
    # --------------------------------------------------
    mortuary_name = Column(String)
    mortuary_phone = Column(String)

    # --------------------------------------------------
    # ✅ NOTES
    # --------------------------------------------------
    special_instructions = Column(Text)

    # --------------------------------------------------
    # ✅ AUDIT (CRITICAL FOR COMPLIANCE)
    # --------------------------------------------------
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )
