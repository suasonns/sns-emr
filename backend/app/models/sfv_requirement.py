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