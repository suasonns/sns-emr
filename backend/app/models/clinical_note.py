from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from app.models.base import BaseModel


class ClinicalNote(BaseModel):
    __tablename__ = "clinical_notes"

    # ===================================================
    # RELATIONSHIPS
    # ===================================================
    visit_id = Column(ForeignKey("visits.id"), nullable=True)
    author_id = Column(ForeignKey("users.id"), nullable=True)

    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)

    # ===================================================
    # CORE CLASSIFICATION
    # ===================================================
    care_level = Column(String(16), nullable=False)
    visit_type = Column(String(32), nullable=False)
    visit_origin = Column(String(32), nullable=False)
    note_category = Column(String(64), nullable=False)
    encounter_type = Column(String(32), nullable=False)
    discipline = Column(String(32), nullable=False)

    # ===================================================
    # LIFECYCLE
    # ===================================================
    status = Column(String(16), nullable=False, server_default=text("'DRAFT'"))
    encounter_date = Column(Date, nullable=False)

    # ✅ FINALIZATION (authoritative)
    finalized_at = Column(DateTime, nullable=True)
    finalized_by = Column(UUID(as_uuid=True), nullable=True)

    # ===================================================
    # CLINICAL DATA (STRUCTURED)
    # ===================================================
    content = Column(Text, nullable=True)  # optional narrative

    observed_data = Column(JSONB, nullable=True)
    patient_reported = Column(JSONB, nullable=True)
    caregiver_reported = Column(JSONB, nullable=True)

    assessment = Column(JSONB, nullable=True)
    interventions = Column(JSONB, nullable=True)
    plan_of_care_updates = Column(JSONB, nullable=True)

    # ===================================================
    # VALIDATION / COMPLIANCE
    # ===================================================
    needs_clarification = Column(JSONB, nullable=True)
    red_flags = Column(JSONB, nullable=True)
    audit_flags = Column(JSONB, nullable=True)

    # ===================================================
    # INCIDENT ENGINE
    # ===================================================
    incident_required = Column(String(1), server_default=text("'0'"))  # store as '0'/'1' for compatibility if needed
    incident_status = Column(String(16), nullable=False, server_default=text("'NONE'"))
    incident_id = Column(UUID(as_uuid=True), nullable=True)

    # ===================================================
    # AUDIT
    # ===================================================
    created_by = Column(UUID(as_uuid=True), nullable=True)
    signed_by = Column(UUID(as_uuid=True), nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    # ===================================================
    # FINALIZE METHOD
    # ===================================================
    def finalize(self, *, user_id):
        if self.finalized_at is not None:
            raise ValueError("Clinical note already finalized")

        self.status = "SIGNED"
        self.finalized_at = datetime.utcnow()
        self.finalized_by = user_id