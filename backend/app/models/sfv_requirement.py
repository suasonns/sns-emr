from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.tenant_mixin import TenantScopedMixin


class SFVRequirement(TenantScopedMixin, BaseModel):
    """SFV requirement + outcome record -- the single authoritative source
    for HOPE J2051/J2052A/J2052B/J2052C and (via `symptom_impact` on the
    completion visit) J2053. Ownership model, permanent reference for
    future changes (do not move J2052C back onto RNICA/Admission/HUV):

    J2051 (Symptom Impact -- creates this requirement)
        Owner: the clinician who authored the triggering RNICA/HUV
        assessment (`trigger_reference_id`). This requirement row does
        NOT give that clinician ownership of any outcome field below --
        the trigger source is read-only once recorded and is never
        mutated by this model or its endpoints.

    J2052A (Was the SFV completed in person?)
        Owner: the SFV clinician (whoever performed or attempted the
        visit). Derived from `status`/`completed_visit_id` vs.
        `reason_recorded_visit_id`.

    J2052B (Date SFV completed)
        Owner: the SFV clinician. Sourced from `completed_at`.

    J2052C (Reason SFV not completed -- CMS codes 1/2/3/9 only)
        Owner: the SFV clinician who attempted the SFV (RN, LVN, LPN,
        NP, On-Call RN, On-Call LVN). Never the RNICA/HUV author. Never
        the Admission owner. Stored on `reason_code`/`reason_recorded_by`/
        `reason_recorded_visit_id` on THIS row, and exported from this
        row (`hopeReportMapper.js`), never from RNICA `form_data`. A
        locked/signed Admission does not block recording this outcome
        because it is a separate row entirely.

    J2053 (Symptom impact after SFV)
        Owner: the SFV completion clinician. Stored in the Visit Note
        (`ClinicalNote.content.symptom_impact` on the completion visit),
        not on this model directly -- unchanged by the J2052C fix
        (issue #146).
    """

    __tablename__ = "sfv_requirements"

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    trigger_source_type = Column(String(32), nullable=False)
    trigger_reference_id = Column(UUID(as_uuid=True), nullable=False)

    trigger_symptom_group = Column(String(16), nullable=False)
    trigger_datetime = Column(DateTime(timezone=True), nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=False)

    task_id = Column(UUID(as_uuid=True), nullable=True)

    completed_visit_id = Column(
        UUID(as_uuid=True),
        ForeignKey("visits.id", ondelete="SET NULL"),
        nullable=True,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    status = Column(
        String(16),
        nullable=False,
        server_default="OPEN",
    )

    notes = Column(Text, nullable=True)

    # HOPE J2052C ownership fix (issue #146): the CMS-coded "reason SFV
    # not completed" outcome, attributed to the clinician who actually
    # attempted the SFV -- NOT the author of the triggering RN
    # ICA/HUV assessment. Populated only when `status` transitions to
    # NOT_COMPLETED via `record_sfv_not_completed_from_visit`. Mirrors
    # `completed_visit_id`/`completed_at`'s existing pattern for the
    # completed branch, so both outcomes are attributed the same way:
    # to the real attempt/completion visit and its clinician, not the
    # trigger source.
    reason_code = Column(String(2), nullable=True)
    reason_recorded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reason_recorded_at = Column(DateTime(timezone=True), nullable=True)
    reason_recorded_visit_id = Column(
        UUID(as_uuid=True),
        ForeignKey("visits.id", ondelete="SET NULL"),
        nullable=True,
    )

    patient = relationship("Patient")
    completed_visit = relationship("Visit", foreign_keys=[completed_visit_id])
    reason_recorded_visit = relationship("Visit", foreign_keys=[reason_recorded_visit_id])

    __table_args__ = (
        CheckConstraint(
            "trigger_source_type IN ('INITIAL_RN_ICA', 'HUV1', 'HUV2')",
            name="ck_sfv_requirements_trigger_source_type",
        ),
        CheckConstraint(
            "trigger_symptom_group IN ('PAIN', 'NON_PAIN', 'BOTH')",
            name="ck_sfv_requirements_trigger_symptom_group",
        ),
        CheckConstraint(
            "status IN ('OPEN', 'COMPLETED', 'OVERDUE', 'CANCELLED', 'NOT_COMPLETED')",
            name="ck_sfv_requirements_status",
        ),
        CheckConstraint(
            "reason_code IS NULL OR reason_code IN ('1', '2', '3', '9')",
            name="ck_sfv_requirements_reason_code",
        ),
        Index(
            "ix_sfv_requirements_open_due",
            "patient_id",
            "status",
            "due_at",
        ),
        Index(
            "uq_sfv_requirements_trigger_once",
            "patient_id",
            "trigger_source_type",
            "trigger_reference_id",
            unique=True,
        ),
    )