# models/rn_recert_assessment.py

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class RNRecertAssessment(Base):
    __tablename__ = "rn_recert_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    benefit_period_id = Column(UUID(as_uuid=True), ForeignKey("benefit_periods.id"), nullable=False, index=True)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # form metadata (keeps it aligned with form-driven architecture)
    form_type = Column(String(50), nullable=False, default="RECERT")
    form_family = Column(String(50), nullable=False, default="CLINICAL")
    discipline = Column(String(50), nullable=False, default="RN")

    # lifecycle
    status = Column(String(20), nullable=False, default="DRAFT", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    finalized_at = Column(DateTime(timezone=True), nullable=True)

    # structured clinical fields
    pps_score = Column(Integer, nullable=True)
    kps_score = Column(Integer, nullable=True)
    fast_stage = Column(String(50), nullable=True)
    nyha_class = Column(String(50), nullable=True)

    adl_level = Column(String(50), nullable=True)
    adl_dependency_count = Column(Integer, nullable=True)

    primary_diagnosis = Column(Text, nullable=True)
    eligibility_recommendation = Column(String(20), nullable=False, default="UNDECIDED")

    # section 34 payloads
    raw_observations_json = Column(JSONB, nullable=False, default=dict)
    clarification_items_json = Column(JSONB, nullable=False, default=list)
    normalized_observations_json = Column(JSONB, nullable=False, default=dict)
    translation_output_json = Column(JSONB, nullable=False, default=dict)
    translation_source_map_json = Column(JSONB, nullable=False, default=dict)
    interpretation_output_json = Column(JSONB, nullable=False, default=dict)

    translation_mode_used = Column(String(20), nullable=False, default="DETERMINISTIC")
    translation_reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    translation_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    translation_accepted = Column(Boolean, nullable=False, default=False)

    attested_at = Column(DateTime(timezone=True), nullable=True)
    attesting_provider_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # relationships (optional; keep small)
    patient = relationship("Patient", foreign_keys=[patient_id])
    benefit_period = relationship("BenefitPeriod", foreign_keys=[benefit_period_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    translation_reviewer = relationship("User", foreign_keys=[translation_reviewed_by])
    attesting_provider = relationship("User", foreign_keys=[attesting_provider_user_id])