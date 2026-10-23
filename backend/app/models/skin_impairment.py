from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class SkinImpairment(Base):
    """
    PRODUCT OWNER DIRECTIVE (2026-11-19/20) "Skin Impairment History /
    Longitudinal Record" -- the stable IDENTITY + LIFECYCLE registry for one
    physical skin impairment (pressure injury, skin tear, surgical wound,
    MASD, etc.) that must persist across every RNICA visit until resolved:
    "unresolved impairments must never disappear between visits. They must
    automatically carry forward to the next RN or LVN assessment until
    resolved."

    This table is DELIBERATELY NOT a duplicate clinical-data store. The
    detailed per-visit clinical assertions (stage, measurements, drainage,
    treatment, photos, notes...) remain exactly where they already live --
    inside each RnicaAssessment.form_data["skin"]["wounds"][] row, keyed by
    this same `id` (the frontend's stable `woundId`, see makeWoundId() in
    RNICA.jsx). This table only tracks WHO/WHAT/WHEN identity and lifecycle
    so a new assessment can discover which impairments are still open and
    auto-carry them forward (see _sync_skin_impairments_from_form_data /
    list_unresolved_skin_impairments in app/api/visits.py), and so Active/
    Resolved views can be served without re-parsing every historical
    assessment's JSONB form_data. One photo/measurement/treatment record,
    multiple indexes -- never a second copy of the clinical detail.
    """

    __tablename__ = "skin_impairments"

    # Primary key IS the frontend's stable woundId (client-generated,
    # collision-resistant string -- see makeWoundId() in RNICA.jsx), not a
    # server-minted uuid, so the same identity can be created/upserted from
    # either the create (/rnica/save) or update (/rnica/{id}) save path
    # without a separate lookup/registration round-trip.
    id = Column(String(64), primary_key=True)

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)

    condition_type = Column(String(64), nullable=False)
    present_as_pressure_injury = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    location = Column(String(128), nullable=True)
    laterality = Column(String(32), nullable=True)

    opened_date = Column(Date, nullable=True)
    opened_visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id", ondelete="SET NULL"), nullable=True)
    opened_assessment_id = Column(UUID(as_uuid=True), ForeignKey("rnica_assessments.id", ondelete="SET NULL"), nullable=True)
    opened_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    opened_by_discipline = Column(String(50), nullable=True)

    # USER-FACING status vocabulary -- PRODUCT OWNER DECISION: keep the
    # legacy HospiceMD terms exactly (New / Existing / Treat / Resolved /
    # COC = Change Of Condition). Do NOT replace this with an internal
    # engineering lifecycle model; if one is ever needed later it must be
    # an ADDITIONAL column, never a replacement of this user-facing value.
    status = Column(String(16), nullable=False, default="New", server_default=text("'New'"), index=True)

    current_stage = Column(String(64), nullable=True)
    current_treatment_summary = Column(Text, nullable=True)

    last_assessment_id = Column(UUID(as_uuid=True), ForeignKey("rnica_assessments.id", ondelete="SET NULL"), nullable=True)
    last_assessment_visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id", ondelete="SET NULL"), nullable=True)
    last_assessment_date = Column(Date, nullable=True)

    # Resolution -- required fields when status transitions to "Resolved".
    # Resolved records are never deleted/hidden: they remain searchable,
    # reportable, and auditable ("Resolved Skin Impairments" view).
    resolved_date = Column(Date, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_by_discipline = Column(String(50), nullable=True)
    resolution_reason = Column(String(64), nullable=True)
    resolution_narrative = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    __table_args__ = (
        Index("ix_skin_impairments_tenant_patient_status", "tenant_id", "patient_id", "status"),
    )
