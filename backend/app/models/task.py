from __future__ import annotations

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base

# ------------------------------------------------------------------
# PostgreSQL enums (already exist in DB — DO NOT recreate)
# ------------------------------------------------------------------
TaskTypeEnum = Enum(
    name="tasks_task_type_enum",
    native_enum=True,
    create_type=False,
)

TaskOriginEnum = Enum(
    name="tasks_origin_enum",
    native_enum=True,
    create_type=False,
)

TaskDisciplineEnum = Enum(
    name="tasks_discipline_enum",
    native_enum=True,
    create_type=False,
)

TaskRegulatoryBasisEnum = Enum(
    name="tasks_regulatory_basis_enum",
    native_enum=True,
    create_type=False,
)

TaskStatusEnum = Enum(
    name="tasks_status_enum",
    native_enum=True,
    create_type=False,
)

TaskCompletionRefEnum = Enum(
    name="tasks_completion_ref_enum",
    native_enum=True,
    create_type=False,
)


class Task(Base):
    """
    Enterprise-grade Task model.

    Regulatory relevance:
    - CMS Hospice Conditions of Participation (CoPs)
    - Survey-defensible obligation lifecycle
    - Evidence-linked completion
    """

    __tablename__ = "tasks"

    # -------------------------------------------------
    # Identity / scope
    # -------------------------------------------------
    id = Column(UUID(as_uuid=True), primary_key=True)

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        nullable=False,
        index=True,
    )

    benefit_period_id = Column(
        UUID(as_uuid=True),
        ForeignKey("benefit_periods.id"),
        nullable=False,
        index=True,
    )

    # -------------------------------------------------
    # Task classification (ENUM enforced by DB)
    # -------------------------------------------------
    task_type = Column(TaskTypeEnum, nullable=False)
    origin = Column(TaskOriginEnum, nullable=False)
    discipline = Column(TaskDisciplineEnum, nullable=False)
    regulatory_basis = Column(TaskRegulatoryBasisEnum, nullable=False)
    status = Column(TaskStatusEnum, nullable=False)

    # -------------------------------------------------
    # Assignment
    # -------------------------------------------------
    assigned_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    # -------------------------------------------------
    # Scheduling
    # -------------------------------------------------
    due_date = Column(Date, nullable=False)

    # -------------------------------------------------
    # Completion evidence (COMPLIANCE‑CRITICAL)
    # -------------------------------------------------
    completed_at = Column(DateTime(timezone=False), nullable=True)

    completion_reference_type = Column(
        TaskCompletionRefEnum,
        nullable=True,
    )

    completion_reference_id = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # -------------------------------------------------
    # Excusal / waiver (audit‑relevant)
    # -------------------------------------------------
    excused_reason_code = Column(String, nullable=True)
    excused_at = Column(DateTime(timezone=True), nullable=True)
    excused_source = Column(String, nullable=True)

    # -------------------------------------------------
    # Audit timestamps
    # -------------------------------------------------
    created_at = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )