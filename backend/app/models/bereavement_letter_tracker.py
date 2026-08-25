# models/bereavement_letter_tracker.py

"""
Bereavement Letters Tracker -- fourth of five planned Bereavement
sub-sections (Initial Assessment, Bereavement POC, Post-Death Assessment,
Bereavement Letters, Post-Death Support).

Purpose: replace the paper/binder-based tracking of the CMS-required
13-month post-death bereavement follow-up contact schedule (COP 418.64(d):
"the hospice must make bereavement services available to the family and
other individuals in the bereavement plan of care for at least 13 months
following the death of the patient... based on the assessment of needs of
the bereaved individual") with a per-touchpoint audit trail: what is due,
when, whether it was sent/completed, by whom, and how -- plus tenant-wide
overdue/due-soon alerting so nothing is missed.

Deliberately kept as its OWN record, separate from BereavementPOC, even
though it is normally seeded from a BereavementPOC's action_plan:
BereavementPOC is a clinical plan-of-care document that gets *signed and
locked* once finalized (see bereavement_poc.py update/sign endpoints, which
reject any PATCH once status == "SIGNED"). But the whole point of this
tracker is to keep recording completions for up to 13 months *after* that
plan is signed -- an operationally "live" record can never be locked the
way a clinical assessment is. Individual items are always editable
regardless of the tracker's own `status`; only whole-tracker discontinuation
(e.g. family requests no further contact) stops new alerts from firing.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base


class BereavementLetterTracker(Base):
    __tablename__ = "bereavement_letter_trackers"

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "ACTIVE")
        kwargs.setdefault("items", [])
        super().__init__(**kwargs)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)

    # Optional links back to the records this tracker was seeded from --
    # never required, so a tracker can be started standalone if a POC
    # doesn't exist yet (e.g. an unexpected death before the POC was
    # finalized).
    bereavement_poc_id = Column(
        UUID(as_uuid=True), ForeignKey("bereavement_pocs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    bereavement_assessment_id = Column(
        UUID(as_uuid=True), ForeignKey("bereavement_assessments.id", ondelete="SET NULL"), nullable=True, index=True
    )

    date_of_death = Column(Date, nullable=True)

    # Risk level snapshot at seed time -- drives which touchpoints were
    # defaulted onto the schedule (HIGH risk adds early check-ins) and is
    # surfaced in the UI/alerts so overdue items can be triaged by risk.
    # Re-synced if the tracker is later re-seeded from an updated POC/
    # Post-Death Assessment risk level via PATCH.
    risk_level = Column(String(16), nullable=True)  # LOW | MODERATE | HIGH

    # ACTIVE (still tracking touchpoints) | COMPLETE (13-month schedule
    # finished) | DISCONTINUED (family opted out / patient family
    # unreachable -- stops generating alerts, but the record and its
    # history are retained for the compliance audit trail).
    status = Column(String(16), nullable=False, index=True)
    discontinued_reason = Column(Text, nullable=True)
    discontinued_at = Column(DateTime(timezone=True), nullable=True)
    discontinued_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # items: [{
    #   key,                 # stable slug, e.g. "d0007_initial_contact_sympathy_card"
    #   month_offset_days,   # days from date_of_death
    #   label,
    #   contact_type,        # LETTER | PHONE | VISIT
    #   required,            # CMS-baseline touchpoint vs clinician-optional
    #   included,            # clinician has this touchpoint active for this family
    #   due_date,            # date_of_death + month_offset_days (or null)
    #   sent_date,           # null until completed
    #   sent_method,         # MAIL | EMAIL | PHONE | IN_PERSON | OTHER
    #   sent_by,             # user id
    #   notes,
    # }, ...]
    items = Column(JSONB, nullable=False)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
