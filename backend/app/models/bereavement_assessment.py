# models/bereavement_assessment.py

"""
Comprehensive Bereavement Assessment (Initial Assessment).

Mirrors the standard hospice bereavement risk-scoring workflow (weighted
checklist -> total score -> LOW/MODERATE/HIGH risk level) used to drive the
Bereavement POC follow-up plan. This is the first of five planned Bereavement
sub-sections (Initial Assessment, Bereavement POC, Post-Death Assessment,
Bereavement Letters, Post-Death Support) -- the others are tracked as
separate follow-up work.

Risk scoring reference (weighted checklist items, see
BEREAVEMENT_RISK_ITEMS in app/services/bereavement_risk_scoring.py):
  - 10 pts: suicide ideation/intent
  - 5 pts: children/adolescents affected
  - 2 pts each: substance abuse history, mental health history, extreme
    dependency, extreme anger/guilt/fear, ambivalent/conflicted
    relationship, family violence history, hopelessness, isolation from
    support system, inadequate coping skills, multiple losses, difficulty
    coping with past losses, traumatic death circumstances, inadequate
    financial resources
  - 1 pt each: pre-existing health concerns, neglect of appearance,
    exhaustion, spiritual distress, unprepared for death, anticipatory
    grief, legal concerns, other (specify)

Risk level thresholds (any single 10-pt item forces HIGH regardless of
total; otherwise total >= 10 is HIGH, >= 5 is MODERATE, else LOW) are a
reasonable default carried over from standard hospice bereavement risk
scales -- adjust if the agency's policy specifies different cutoffs.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base


class BereavementAssessment(Base):
    __tablename__ = "bereavement_assessments"

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "DRAFT")
        kwargs.setdefault("risk_items", {})
        kwargs.setdefault("additional_bereaved", [])
        super().__init__(**kwargs)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(String(16), nullable=False, server_default=text("'DRAFT'"), index=True)  # DRAFT | SIGNED

    # ---------------------------------------------------------
    # Visit metadata
    # ---------------------------------------------------------
    entered_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    staff_assigned = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    discipline = Column(String(16), nullable=True)  # e.g. BSW, MSW, RN, Chaplain
    care_level = Column(String(16), nullable=True)  # RC, GIP, CC, RESPITE
    visit_type = Column(String(16), nullable=True)  # IN_PERSON | TELEPHONE
    visit_mode = Column(String(16), nullable=True)  # SCHEDULED | UNSCHEDULED
    visit_date = Column(Date, nullable=True)
    time_in = Column(String(8), nullable=True)
    time_out = Column(String(8), nullable=True)
    duration_minutes = Column(Integer, nullable=True)

    # ---------------------------------------------------------
    # Primary bereaved
    # ---------------------------------------------------------
    no_family = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    primary_first_name = Column(String(128), nullable=True)
    primary_last_name = Column(String(128), nullable=True)
    primary_age = Column(Integer, nullable=True)
    primary_gender = Column(String(32), nullable=True)
    primary_address = Column(String(255), nullable=True)
    primary_city = Column(String(128), nullable=True)
    primary_state = Column(String(64), nullable=True)
    primary_zip = Column(String(16), nullable=True)
    primary_home_phone = Column(String(32), nullable=True)
    primary_work_phone = Column(String(32), nullable=True)
    primary_cell_phone = Column(String(32), nullable=True)
    primary_email = Column(String(255), nullable=True)
    primary_relationship_to_patient = Column(String(128), nullable=True)
    primary_was_caregiver = Column(Boolean, nullable=True)

    # ---------------------------------------------------------
    # Risk scoring -- see BEREAVEMENT_RISK_ITEMS for the item catalog.
    # risk_items: {item_key: {"checked": bool, "note": str | None}}
    # ---------------------------------------------------------
    risk_items = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    risk_other_note = Column(Text, nullable=True)
    risk_total_score = Column(Integer, nullable=False, default=0, server_default=text("0"))
    risk_level = Column(String(16), nullable=True)  # LOW | MODERATE | HIGH

    # ---------------------------------------------------------
    # Additional bereaved: [{name, relationship_to_patient, address, phone, specific_concerns}]
    # ---------------------------------------------------------
    additional_bereaved = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))

    narrative = Column(Text, nullable=True)

    # ---------------------------------------------------------
    # Signature
    # ---------------------------------------------------------
    signed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
