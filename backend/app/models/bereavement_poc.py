# models/bereavement_poc.py

"""
Bereavement Plan of Care (POC) -- second of five planned Bereavement
sub-sections (see chart-section-bereavement-poc). Translates the risk level
from a Comprehensive Bereavement Assessment into a concrete, risk-tiered set
of goals/interventions plus the CMS-required 13-month bereavement follow-up
contact schedule (COPs 418.64(d): bereavement services must be available to
the family for at least 13 months following the patient's death).

Kept as its own record (rather than folded into BereavementAssessment) so a
POC can be created, revised, and signed independently of the assessment that
informed it, and so the 13-month action plan can be checked off over time
without reopening/unlocking a signed assessment.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base


class BereavementPOC(Base):
    __tablename__ = "bereavement_pocs"

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "DRAFT")
        kwargs.setdefault("goals", [])
        kwargs.setdefault("interventions", [])
        kwargs.setdefault("action_plan", [])
        super().__init__(**kwargs)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)

    # Optional link back to the assessment this POC was generated from -- not
    # required, since a POC can be started/updated independently later.
    bereavement_assessment_id = Column(
        UUID(as_uuid=True), ForeignKey("bereavement_assessments.id", ondelete="SET NULL"), nullable=True, index=True
    )

    status = Column(String(16), nullable=False, index=True)  # DRAFT | SIGNED

    entered_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    staff_assigned = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    discipline = Column(String(16), nullable=True)

    date_of_death = Column(Date, nullable=True)
    risk_level = Column(String(16), nullable=True)  # LOW | MODERATE | HIGH
    # Provenance of risk_level: SCORED (inherited from a linked, weighted-score
    # BereavementAssessment) vs MANUAL (clinician picked it directly on the
    # POC with no scored assessment backing it). Surfaced in the UI so a
    # manually-set risk level can never be mistaken for a scored one.
    risk_source = Column(String(16), nullable=True)  # SCORED | MANUAL
    # Snapshot of the linked assessment's total score at the time risk_level
    # was inherited, kept for audit/traceability even if the assessment is
    # later edited or unlinked.
    risk_score = Column(Integer, nullable=True)

    # ---------------------------------------------------------
    # Primary bereaved -- mirrors BereavementAssessment's primary-bereaved
    # fields so a POC can stand alone (no linked assessment) and still record
    # who the plan is for. When bereavement_assessment_id is set and these
    # are not explicitly supplied, they are copied from the linked
    # assessment at create time.
    # ---------------------------------------------------------
    no_family = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    primary_first_name = Column(String(128), nullable=True)
    primary_last_name = Column(String(128), nullable=True)
    primary_relationship_to_patient = Column(String(128), nullable=True)
    primary_address = Column(String(255), nullable=True)
    primary_city = Column(String(128), nullable=True)
    primary_state = Column(String(64), nullable=True)
    primary_zip = Column(String(16), nullable=True)
    primary_home_phone = Column(String(32), nullable=True)
    primary_cell_phone = Column(String(32), nullable=True)
    primary_email = Column(String(255), nullable=True)
    primary_was_caregiver = Column(Boolean, nullable=True)

    # goals: [{key, label, selected, target_date, notes}]
    goals = Column(JSONB, nullable=False)
    # interventions: [{key, label, selected, notes}]
    interventions = Column(JSONB, nullable=False)
    # Freeform "Other Interventions -- specify" text, matching standard
    # hospice bereavement POC forms.
    other_interventions = Column(Text, nullable=True)
    # action_plan (13-month contact schedule):
    # [{month_offset_days, label, contact_type, required, included,
    #   planned_date, completed_date, completed_by, notes}]
    action_plan = Column(JSONB, nullable=False)

    narrative = Column(Text, nullable=True)

    closed_early = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    closed_reason = Column(Text, nullable=True)

    signed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
