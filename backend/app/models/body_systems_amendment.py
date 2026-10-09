from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.base import BaseModel

# Reused, NOT redefined: the same correction/amendment taxonomy already
# governing RNICA's SECTION 12 Amendment Infrastructure
# (app/models/rnica_amendment.py). Importing rather than duplicating keeps
# the two amendment workflows semantically identical (same categories,
# reason codes, request sources, statuses) so compliance reporting can
# treat them as one taxonomy across systems.
from app.models.rnica_amendment import (  # noqa: F401 (re-exported for callers)
    AMENDMENT_CATEGORIES,
    AMENDMENT_REASON_CODES,
    AMENDMENT_REQUEST_SOURCES,
    AMENDMENT_STATUSES,
)


class BodySystemsAmendment(BaseModel):
    """Body Systems correction/amendment infrastructure.

    Mirrors the SECTION 12 `RnicaAmendment` "never destroy, always append"
    guarantee -- the same precedent already followed for
    `SfvOutcomeCorrection` (app/models/sfv_outcome_correction.py) when an
    entity other than a locked RN ICA assessment needed this protection.
    A dedicated sibling table (rather than generalizing the live, already-
    shipped `rnica_amendments` table) is used deliberately: `RnicaAmendment.
    rnica_assessment_id` is NOT NULL with ON DELETE CASCADE, directly
    modeling a 1:1 coupling to `rnica_assessments`. Relaxing that column to
    nullable and introducing a second, mutually-exclusive foreign key would
    change the referential-integrity contract of an existing, tested,
    production RNICA workflow for no compliance benefit -- the documented
    incompatibility this module resolves by following the SFV precedent
    instead of generalizing RNICA's table.

    A `BodySystemsAmendment` row is ALWAYS appended alongside the
    `SystemAssessment` it concerns and NEVER overwrites it --
    `system_assessments.data`/`summary`/limitation fields are never mutated
    by this workflow. Deciding an amendment only changes this row's
    `status`/`decision_user_id`/`decision_timestamp`/`decision_reason`; it
    does not retroactively apply `proposed_value` back onto the original
    content (identical behavior to RNICA amendments).
    """

    __tablename__ = "body_systems_amendments"

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    system_assessment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("system_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Denormalized copy of system_assessments.system (e.g. "respiratory").
    # Stored directly -- not joined on every read -- so compliance/export
    # queries can filter amendments by body system without a join, matching
    # the existing system_assessments.system / review_exceptions.system
    # denormalization convention already used in app/models/body_systems.py.
    system = Column(String(32), nullable=False, index=True)

    # Which field/section within the system this amendment concerns, e.g.
    # "limitation.timingOrContingency" or "data.oxygenSaturation". Nullable:
    # some amendments concern the system assessment as a whole.
    field_reference = Column(String(128), nullable=True)

    # CLINICAL_CORRECTION | ADDITIONAL_FINDING | DOCUMENTATION_ERROR |
    # CLARIFICATION | OTHER (see AMENDMENT_CATEGORIES)
    amendment_category = Column(String(32), nullable=False, index=True)

    # OMITTED_FINDING | INCORRECT_VALUE | CLARIFICATION_NEEDED |
    # LATE_ENTRY | OTHER (see AMENDMENT_REASON_CODES)
    reason_code = Column(String(32), nullable=False)

    # Free-text rationale describing what should change and why.
    requested_change = Column(Text, nullable=False)

    # Point-in-time snapshot of the originally documented value, captured
    # at submission time so the amendment remains fully self-contained and
    # traceable even if the underlying field is later re-documented.
    original_value_snapshot = Column(JSONB, nullable=True)

    # The clinician's proposed replacement value/text. Never auto-applied.
    proposed_value = Column(JSONB, nullable=True)

    # PATIENT | REPRESENTATIVE | STAFF | INTERNAL_QA -- who originated the
    # request (see AMENDMENT_REQUEST_SOURCES).
    request_source = Column(String(16), nullable=False, server_default="STAFF")

    # PENDING | APPROVED | DENIED (see AMENDMENT_STATUSES)
    status = Column(String(16), nullable=False, server_default="PENDING", index=True)

    # Unified decision metadata -- applies to either disposition. For
    # DENIED, decision_reason is required (written justification); for
    # APPROVED it is optional context.
    decision_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    decision_timestamp = Column(DateTime(timezone=True), nullable=True)
    decision_reason = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_body_systems_amendments_assessment_status", "system_assessment_id", "status"),
        Index("ix_body_systems_amendments_patient_status", "patient_id", "status"),
    )
