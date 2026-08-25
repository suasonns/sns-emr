# models/bereavement_communication_note.py

"""
Bereavement Communication Note -- append-only contact log for the fifth and
final Bereavement sub-section (Post-Death Bereavement Support; see
chart-section-bereavement-support). Replaces the free-text "contact log"
pages of the paper bereavement binder with a structured, immutable record of
every phone call / visit / letter / email exchanged with the bereaved family
during the 13-month CMS COP 418.64(d) follow-up period.

Deliberately append-only (no update/delete API): once a contact is logged it
is part of the permanent record, matching how the rest of the chart treats
clinical/communication entries as an audit trail rather than an editable
document. Distinct from BereavementLetterTracker, which tracks *scheduled,
required* touchpoints against due dates -- this table captures the actual
narrative of what was said/discussed on any contact, scheduled or not (e.g.
an unplanned call from a grieving spouse), and can optionally be tied back to
a specific tracker touchpoint for traceability.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class BereavementCommunicationNote(Base):
    __tablename__ = "bereavement_communication_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)

    # Optional link to the specific scheduled touchpoint this contact
    # fulfilled/relates to -- purely informational, never required, since
    # many contacts (e.g. a family-initiated call) don't map to a scheduled
    # item.
    bereavement_letter_tracker_id = Column(
        UUID(as_uuid=True), ForeignKey("bereavement_letter_trackers.id", ondelete="SET NULL"), nullable=True
    )

    contact_date = Column(Date, nullable=False, index=True)
    contact_type = Column(String(16), nullable=False)  # PHONE | VISIT | LETTER | EMAIL | OTHER
    contact_with = Column(String(255), nullable=True)  # e.g. "Primary bereaved -- Jane Doe"
    summary = Column(Text, nullable=False)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
