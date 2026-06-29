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

    patient = relationship("Patient")
    completed_visit = relationship("Visit", foreign_keys=[completed_visit_id])

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
            "status IN ('OPEN', 'COMPLETED', 'OVERDUE', 'CANCELLED')",
            name="ck_sfv_requirements_status",
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