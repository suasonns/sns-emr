from __future__ import annotations

import uuid

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Text,                # ✅ REQUIRED
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

# ✅ CANONICAL ENUMS (DO NOT RENAME)
from app.models.enums import (
    TaskType,
    TaskOrigin,
    TaskDiscipline,
    TaskRegulatoryBasis,
    TaskStatus,
    CompletionReferenceType,
)


class Task(Base):
    __tablename__ = "tasks"

    # =====================================================
    # PRIMARY KEY
    # =====================================================
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # =====================================================
    # CORE RELATIONSHIP KEYS
    # =====================================================
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    benefit_period_id = Column(
        UUID(as_uuid=True),
        ForeignKey("benefit_periods.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    assigned_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    # =====================================================
    # LINKING (CRITICAL FOR WORKFLOW ENGINE)
    # =====================================================
    clinical_note_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clinical_notes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    incident_id = Column(
        UUID(as_uuid=True),
        ForeignKey("incident_reports.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # =====================================================
    # TASK CLASSIFICATION
    # =====================================================
    task_type = Column(
        SAEnum(TaskType, create_type=False),
        nullable=False,
    )

    origin = Column(
        SAEnum(TaskOrigin, create_type=False),
        nullable=False,
    )

    discipline = Column(
        SAEnum(TaskDiscipline, create_type=False),
        nullable=False,
    )

    regulatory_basis = Column(
        SAEnum(TaskRegulatoryBasis, create_type=False),
        nullable=True,
    )

    # =====================================================
    # ✅ CRITICAL FIX — ALERT REASON COLUMN
    # =====================================================
    alert_reason = Column(Text, nullable=True)

    # =====================================================
    # STATUS
    # =====================================================
    status = Column(
        SAEnum(TaskStatus, create_type=False),
        nullable=False,
        server_default=text("'DUE'"),
    )

    # =====================================================
    # DUE TIMING
    # =====================================================
    due_date = Column(Date, nullable=True)

    due_at = Column(DateTime(timezone=True), nullable=True)

    # =====================================================
    # COMPLETION (AUDIT SAFE)
    # =====================================================
    completed_at = Column(DateTime(timezone=True), nullable=True)

    completion_reference_type = Column(
        SAEnum(CompletionReferenceType, create_type=False),
        nullable=True,
    )

    completion_reference_id = Column(UUID(as_uuid=True), nullable=True)

    # =====================================================
    # AUDIT
    # =====================================================
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================
    patient = relationship("Patient", back_populates="tasks")

    benefit_period = relationship("BenefitPeriod", back_populates="tasks")

    created_by_user = relationship(
        "User",
        foreign_keys=[created_by],
    )

    assigned_user = relationship(
        "User",
        foreign_keys=[assigned_user_id],
    )