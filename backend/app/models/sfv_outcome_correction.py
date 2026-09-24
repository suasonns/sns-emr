from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class SfvOutcomeCorrection(BaseModel):
    """HOPE J2052C ownership fix (issue #146).

    Append-only correction record for `SFVRequirement.reason_code`,
    mirroring the SECTION 12 `RnicaAmendment` "never destroy, always
    append" guarantee -- but scoped to the SFV requirement (a live
    operational record) rather than a locked/signed RN ICA assessment.
    Every correction to a previously-recorded J2052C reason code inserts
    one of these rows BEFORE the live `reason_code` value is updated, so
    the prior value is always recoverable and the change is always
    attributable (who, when, why). Never deletes or overwrites a prior
    correction row.
    """

    __tablename__ = "sfv_outcome_corrections"

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sfv_requirement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sfv_requirements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    prior_reason_code = Column(String(2), nullable=True)
    new_reason_code = Column(String(2), nullable=False)

    correction_reason = Column(Text, nullable=False)

    corrected_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    corrected_at = Column(DateTime(timezone=True), nullable=False)
