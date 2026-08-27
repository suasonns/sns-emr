from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class CCHourlyNarrativeEntry(Base):
    """
    One row per hourly (or per-shift) documentation entry captured while a
    patient is at the Continuous Care (CC) level of care. This is the
    shared CC form referenced by app.domain.forms.form_registry
    (PRIMARY_CC_HOURLY_NARRATIVE / MOD_CC_ENTRY) -- the same form is used
    across RN, LVN, AIDE (CHHA), MSW, and Chaplain visits; only the
    `discipline` on each entry differs.
    """

    __tablename__ = "cc_hourly_narrative_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id"), nullable=False, index=True)

    discipline = Column(String(32), nullable=False)  # RN, LVN, AIDE, MSW, CHAPLAIN

    entry_date = Column(String(16), nullable=True)
    entry_time = Column(String(16), nullable=True)

    # ── Vitals ──
    temperature = Column(String(16), nullable=True)
    pulse = Column(String(16), nullable=True)
    respirations = Column(String(16), nullable=True)
    bp_systolic = Column(String(16), nullable=True)
    bp_diastolic = Column(String(16), nullable=True)
    o2_sat = Column(String(16), nullable=True)

    # ── Pain ──
    pain_level = Column(String(8), nullable=True)
    pain_location = Column(String(255), nullable=True)
    pain_intervention = Column(Text, nullable=True)

    # ── Symptoms / care provided ──
    symptoms = Column(Text, nullable=True)
    care_provided = Column(Text, nullable=True)

    # ── Issue management ──
    issue_identified = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    issue_narrative = Column(Text, nullable=True)

    # ── Plan of care update ──
    poc_update_narrative = Column(Text, nullable=True)

    # ── General narrative ──
    narrative = Column(Text, nullable=True)

    entered_by = Column(String(255), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    created_by = Column(UUID(as_uuid=True), nullable=True)

    visit = relationship("Visit", backref="cc_hourly_narrative_entries")
