# backend/app/models/task.py

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Text,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

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
    # LINKING
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

    alert_reason = Column(Text, nullable=True)

    # =====================================================
    # STATUS
    # =====================================================
    status = Column(
        SAEnum(TaskStatus, create_type=False),
        nullable=False,
        server_default=text("'PENDING'"),
    )

    # ✅ INTELLIGENCE FIELDS (FINAL)
    priority = Column(String, nullable=True)
    clinical_severity = Column(String, nullable=True)

    # ✅ ROUTING + NOTIFICATION (FINAL FIX)
    assigned_role = Column(String, nullable=True)
    notification_required = Column(Boolean, nullable=False, server_default="false")
    
    
    # ✅ TRACEABILITY (FINAL FIX)
    reference_type = Column(String, nullable=True)
    reference_id = Column(UUID(as_uuid=True), nullable=True)

    # =====================================================
    # DUE TIMING
    # =====================================================
    due_date = Column(Date, nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)

    # =====================================================
    # SLA ENGINE
    # =====================================================
    sla_start_at = Column(DateTime(timezone=True), nullable=True)
    sla_due_at = Column(DateTime(timezone=True), nullable=True)

    is_overdue = Column(Boolean, nullable=False, server_default="false")

    escalation_level = Column(Integer, nullable=False, server_default="0")
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    escalation_reason = Column(Text, nullable=True)

    # =====================================================
    # COMPLETION
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

    created_by_user = relationship("User", foreign_keys=[created_by])

    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
