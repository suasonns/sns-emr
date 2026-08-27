# models/post_death_bereavement_assessment.py

"""
Post-Death Bereavement Assessment -- third of five planned Bereavement
sub-sections (Initial Assessment, Bereavement POC, Post-Death Assessment,
Bereavement Letters, Post-Death Support).

Conducted after the patient's death to: (1) capture death facts and
condolence-call follow-up, (2) re-score bereavement risk using the same
weighted checklist as the Initial Assessment (see
app/services/bereavement_risk_scoring.py) since grief risk can change
materially after the death itself, and (3) record a fresh goals/interventions
plan-of-care reflecting the reassessed risk level. Optionally linked back to
the Initial Assessment and/or the Bereavement POC so the primary bereaved
contact only has to be entered once and so the UI can show how risk has
shifted since the initial (pre-death) assessment.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base


class PostDeathBereavementAssessment(Base):
    __tablename__ = "post_death_bereavement_assessments"

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "DRAFT")
        kwargs.setdefault("risk_items", {})
        kwargs.setdefault("goals", [])
        kwargs.setdefault("interventions", [])
        super().__init__(**kwargs)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(String(16), nullable=False, index=True)  # DRAFT | SIGNED

    # Optional links -- used to inherit primary-bereaved contact info and to
    # show risk-level drift ("was HIGH at initial assessment, now MODERATE").
    bereavement_assessment_id = Column(
        UUID(as_uuid=True), ForeignKey("bereavement_assessments.id", ondelete="SET NULL"), nullable=True
    )
    bereavement_poc_id = Column(UUID(as_uuid=True), ForeignKey("bereavement_pocs.id", ondelete="SET NULL"), nullable=True)

    # ---------------------------------------------------------
    # Visit metadata
    # ---------------------------------------------------------
    entered_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    staff_assigned = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    discipline = Column(String(16), nullable=True)
    visit_type = Column(String(16), nullable=True)  # IN_PERSON | TELEPHONE
    visit_mode = Column(String(16), nullable=True)  # SCHEDULED | UNSCHEDULED
    visit_date = Column(Date, nullable=True)
    time_in = Column(String(8), nullable=True)
    time_out = Column(String(8), nullable=True)
    duration_minutes = Column(Integer, nullable=True)

    # ---------------------------------------------------------
    # Primary bereaved -- inherited from the linked assessment/POC when not
    # supplied explicitly (same field set/naming as BereavementAssessment and
    # BereavementPOC for consistency).
    # ---------------------------------------------------------
    no_family = Column(Boolean, nullable=False, default=False)
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

    # ---------------------------------------------------------
    # Death facts
    # ---------------------------------------------------------
    date_of_death = Column(Date, nullable=True)
    place_of_death = Column(String(32), nullable=True)  # HOME | INPATIENT_HOSPICE | HOSPITAL | NURSING_FACILITY | OTHER
    death_expected = Column(Boolean, nullable=True)
    pcg_present_at_death = Column(Boolean, nullable=True)
    family_present_at_death = Column(Boolean, nullable=True)
    funeral_plans_finalized = Column(Boolean, nullable=True)
    funeral_home_name = Column(String(255), nullable=True)

    # ---------------------------------------------------------
    # Condolence call
    # ---------------------------------------------------------
    condolence_call_date = Column(Date, nullable=True)
    condolence_call_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    condolence_call_notes = Column(Text, nullable=True)

    # PCG/family emotional status & coping at time of this assessment.
    emotional_status_narrative = Column(Text, nullable=True)

    # ---------------------------------------------------------
    # Post-death reassessment questions
    # ---------------------------------------------------------
    survivor_support_system_adequate = Column(Boolean, nullable=True)
    desires_intensive_bereavement_support = Column(Boolean, nullable=True)
    complicated_grief_reactions_observed = Column(Boolean, nullable=True)
    additional_risk_factors_since_initial = Column(Boolean, nullable=True)
    additional_risk_notes = Column(Text, nullable=True)

    # ---------------------------------------------------------
    # Risk re-scoring -- same weighted catalog/algorithm as the Initial
    # Assessment (see BEREAVEMENT_RISK_ITEMS / score_bereavement_risk), scored
    # independently here since grief risk commonly shifts after the death.
    # ---------------------------------------------------------
    risk_items = Column(JSONB, nullable=False)
    risk_other_note = Column(Text, nullable=True)
    risk_total_score = Column(Integer, nullable=False, default=0)
    risk_level = Column(String(16), nullable=True)  # LOW | MODERATE | HIGH

    # ---------------------------------------------------------
    # Goals / interventions plan of care, reflecting the reassessed risk
    # level (defaults sourced from the same risk-tiered catalog used by the
    # Bereavement POC; see bereavement_poc_catalog.default_goals_for_risk /
    # default_interventions_for_risk).
    # ---------------------------------------------------------
    goals = Column(JSONB, nullable=False)
    interventions = Column(JSONB, nullable=False)
    other_interventions = Column(Text, nullable=True)
    plan_of_care_narrative = Column(Text, nullable=True)

    narrative = Column(Text, nullable=True)

    # ---------------------------------------------------------
    # Signature
    # ---------------------------------------------------------
    signed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
