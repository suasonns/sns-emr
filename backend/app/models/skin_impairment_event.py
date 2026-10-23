from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class SkinImpairmentEvent(Base):
    """
    PRODUCT OWNER DIRECTIVE "Longitudinal Wound Record" (2026-11-21) --
    "Capture all wound events. Capture treatment history. Capture photo
    history. Capture COC history. Capture resolution history. Design the
    database so future clinical decision support can analyze wound
    trajectories. Do NOT build treatment recommendation logic in this
    RNICA phase."

    PRODUCT OWNER REVIEW (2026-11-21 follow-up) -- "Do not design events
    as wound-specific. Design events as longitudinal clinical events...
    the same event model should be reusable later for Medications, Orders,
    Treatments, DME, Supplies, Falls, Nutrition, Pain, Functional Decline,
    HOPE... one longitudinal clinical history model with multiple future
    modules." No additional scope is approved to build that generic model
    now (a polymorphic `clinical_events` table is explicitly deferred,
    same as QAPI/Supply/Cost) -- this phase only has to guarantee that
    THIS table's shape never has to be rewritten to get there. Every row
    already carries the seven fields the Product Owner named as mandatory
    for any future clinical event, under these exact column names:
      eventId          -> id
      eventType        -> event_type
      patientId        -> patient_id
      visitId          -> visit_id
      assessmentId     -> assessment_id
      createdBy        -> recorded_by
      discipline       -> recorded_by_discipline
      eventTimestamp   -> recorded_at
    The only module-specific parts are `skin_impairment_id` (the subject
    FK -- would become a polymorphic subject_type/subject_id pair in a
    future generalized model) and the wound-domain detail columns below
    (stage/measurements/drainage/treatment_summary/photo_id/coc_reason/
    resolution_*). A future generalization can therefore split this exact
    row shape into a generic `clinical_events` header plus a per-module
    detail table without discarding or renaming any data captured now.

    This is the append-only EVENT LOG for one SkinImpairment (one row per
    clinically meaningful occurrence against that impairment, newest
    appended -- never updated into a different meaning, never deleted).
    `SkinImpairment` remains the current-state/identity registry; this
    table is its full history, purpose-built so a future clinical-decision
    -support feature can walk one impairment's `event_date` timeline and
    compare an EXPECTED trajectory to the OBSERVED one (stage/measurement/
    drainage/status over time) WITHOUT re-parsing every historical RNICA
    assessment's JSONB form_data. No recommendation/interpretation logic
    lives here or anywhere in this phase -- only the structured history
    such a feature would eventually read.

    Event types (`event_type`):
      - "assessment": this visit's wound snapshot (stage/measurements/
        drainage/odor/etc.) -- one per (impairment, assessment).
      - "treatment": a treatment/dressing change or continuation was
        documented this visit.
      - "photo": a photo was added (metadata only -- the image itself
        stays exactly where it already lives, inside that visit's
        form_data wound.photos[] entry; see `photo_id`).
      - "status_change": the user-facing status (New/Existing/Treat/
        Resolved/COC) changed from one visit's save to the next.
      - "coc": a Change Of Condition was documented (a status_change
        event also fires alongside this when status transitions to COC).
      - "resolution": status transitioned TO "Resolved".
      - "reopened": status transitioned AWAY FROM "Resolved" (a
        previously resolved impairment became active again).
      - "poc_change": a plan-of-care change was documented against this
        impairment (reserved for future POC-integration wiring).
      - "provider_notification": a provider was notified regarding this
        impairment (reserved for future notification wiring).

    One event per (impairment, assessment, event_type[, photo_id]) is
    upserted rather than duplicated across repeated autosaves of the same
    visit -- see the unique index below and `_sync_skin_impairments_from_
    form_data` in app/api/visits.py.
    """

    __tablename__ = "skin_impairment_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    skin_impairment_id = Column(
        String(64), ForeignKey("skin_impairments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Denormalized for direct patient/tenant-scoped trajectory queries
    # without a join back through skin_impairments.
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)

    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id", ondelete="SET NULL"), nullable=True)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("rnica_assessments.id", ondelete="SET NULL"), nullable=True)

    event_type = Column(String(32), nullable=False, index=True)
    # Clinical date the event pertains to (assessment/visit date), distinct
    # from `recorded_at` (system timestamp the row was written).
    event_date = Column(Date, nullable=True)
    recorded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )
    recorded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    recorded_by_discipline = Column(String(50), nullable=True)

    # Status-over-time -- the backbone of a future trajectory view.
    status = Column(String(16), nullable=True)
    previous_status = Column(String(16), nullable=True)

    # Structured, numeric trajectory fields (deliberately discrete columns,
    # not a JSON blob, so future analysis can trend/aggregate them
    # directly -- e.g. "wound area over time" -- without JSON parsing).
    stage = Column(String(64), nullable=True)
    measurement_length_cm = Column(Numeric(6, 2), nullable=True)
    measurement_width_cm = Column(Numeric(6, 2), nullable=True)
    measurement_depth_cm = Column(Numeric(6, 2), nullable=True)
    drainage_amount = Column(String(32), nullable=True)
    drainage_character = Column(String(64), nullable=True)
    odor = Column(String(32), nullable=True)
    surrounding_skin = Column(String(64), nullable=True)

    # Treatment-event detail.
    treatment_summary = Column(Text, nullable=True)

    # Photo-event detail -- metadata only; see class docstring. Stored as
    # "" (never NULL) for every non-photo event type so the natural-key
    # unique index below actually dedupes them -- Postgres treats each
    # NULL in a unique index as distinct, which would otherwise allow
    # unlimited duplicate assessment/treatment/status rows per visit.
    photo_id = Column(String(64), nullable=False, default="", server_default=text("''"))

    # COC-event detail.
    coc_reason = Column(Text, nullable=True)

    # Resolution/reopened-event detail (denormalized snapshot at the time
    # of the event, independent of whatever SkinImpairment.resolution_*
    # holds later -- e.g. after a reopen clears it).
    resolution_reason = Column(String(64), nullable=True)
    resolution_narrative = Column(Text, nullable=True)

    # Reserved for future POC-integration / provider-notification wiring
    # (PRODUCT OWNER: "POC changes", "Provider notifications" must be
    # part of what this longitudinal record is designed to capture).
    poc_change_summary = Column(Text, nullable=True)
    provider_notified = Column(Boolean, nullable=True)
    provider_notified_name = Column(String(128), nullable=True)

    notes = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    __table_args__ = (
        Index("ix_skin_impairment_events_impairment_date", "skin_impairment_id", "event_date"),
        Index("ix_skin_impairment_events_tenant_patient_type", "tenant_id", "patient_id", "event_type"),
        Index(
            "uq_skin_impairment_events_natural_key",
            "skin_impairment_id", "assessment_id", "event_type", "photo_id",
            unique=True,
        ),
    )
