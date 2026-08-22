from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.base import BaseModel


# Broad classification of what kind of correction/addendum is being made.
AMENDMENT_CATEGORIES = (
    "CLINICAL_CORRECTION",
    "ADDITIONAL_FINDING",
    "DOCUMENTATION_ERROR",
    "CLARIFICATION",
    "OTHER",
)

# Specific reason code within the chosen category.
AMENDMENT_REASON_CODES = (
    "OMITTED_FINDING",
    "INCORRECT_VALUE",
    "CLARIFICATION_NEEDED",
    "LATE_ENTRY",
    "OTHER",
)

# PENDING -> APPROVED | DENIED. There is no auto-approval and no
# intermediate states -- a review authority (see AMENDMENT_APPROVAL_ROLES
# in app/api/visits.py) must explicitly decide.
AMENDMENT_STATUSES = ("PENDING", "APPROVED", "DENIED")


class RnicaAmendment(BaseModel):
    """SECTION 12 -- Amendment Infrastructure.

    A distinct, timestamped, attributable correction/addendum entry
    attached to an already-locked (signed) RN ICA assessment. Per the
    frozen master map ("Correction / amendment path"), an amendment is
    ALWAYS appended alongside the signed record and NEVER overwrites it:
    `rnica_assessments.form_data` for a locked assessment is never mutated
    by this workflow. Approving an amendment only changes this row's
    `status`/`approved_by`/`approved_at` -- it does not retroactively
    apply `proposed_value` back onto the original signed content.
    """

    __tablename__ = "rnica_amendments"

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    rnica_assessment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rnica_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Which RN ICA section/field this amendment concerns, e.g. "nutrition"
    # or "diagnoses.clinicalNarrative". Nullable: some amendments concern
    # the assessment as a whole rather than one section.
    section_reference = Column(String(128), nullable=True)

    # CLINICAL_CORRECTION | ADDITIONAL_FINDING | DOCUMENTATION_ERROR |
    # CLARIFICATION | OTHER
    amendment_category = Column(String(32), nullable=False, index=True)

    # OMITTED_FINDING | INCORRECT_VALUE | CLARIFICATION_NEEDED |
    # LATE_ENTRY | OTHER
    reason_code = Column(String(32), nullable=False)

    # Free-text rationale describing what should change and why.
    requested_change = Column(Text, nullable=False)

    # Point-in-time snapshot of the originally documented value, captured
    # at submission time so the amendment remains fully self-contained and
    # traceable even if the underlying section is later re-documented.
    original_value_snapshot = Column(JSONB, nullable=True)

    # The clinician's proposed replacement value/text. Never auto-applied.
    proposed_value = Column(JSONB, nullable=True)

    # PENDING | APPROVED | DENIED
    status = Column(String(16), nullable=False, server_default="PENDING", index=True)

    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    denied_reason = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_rnica_amendments_assessment_status", "rnica_assessment_id", "status"),
        Index("ix_rnica_amendments_patient_status", "patient_id", "status"),
    )
