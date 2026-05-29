# app/models/task.py

from __future__ import annotations

import uuid
from sqlalchemy import Column, Date, DateTime, Enum as SAEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base

# Canonical enums (DO NOT rename these)
from app.models.enums import (
    TaskType,
    TaskOrigin,
    TaskDiscipline,
    TaskRegulatoryBasis,
    TaskStatus,
    CompletionReferenceType,
)


class Task(Base):
    """
    Enterprise-grade Task model.

    Regulatory relevance:
    - CMS Hospice CoPs obligation lifecycle
    - Survey-defensible obligation tracking
    - Evidence-linked completion
    """

    __tablename__ = "tasks"

    # -------------------------------------------------
    # Identity
    # -------------------------------------------------
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # -------------------------------------------------
    # Tenant isolation (NON-NEGOTIABLE)
    # -------------------------------------------------
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # -------------------------------------------------
    # Scope / attribution
    # -------------------------------------------------
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Nullable by design (benefit periods may not exist yet in dev)
    benefit_period_id = Column(
        UUID(as_uuid=True),
        ForeignKey("benefit_periods.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    # -------------------------------------------------
    # Task classification (PostgreSQL ENUM + Python Enum)
    # -------------------------------------------------
    task_type = Column(
        SAEnum(
            TaskType,
            name="tasks_task_type_enum",
            native_enum=True,
            create_type=False,
        ),
        nullable=False,
    )

    origin = Column(
        SAEnum(
            TaskOrigin,
            name="tasks_origin_enum",
            native_enum=True,
            create_type=False,
        ),
        nullable=False,
    )

    discipline = Column(
        SAEnum(
            TaskDiscipline,
            name="tasks_discipline_enum",
            native_enum=True,
            create_type=False,
        ),
        nullable=False,
    )

    regulatory_basis = Column(
        SAEnum(
            TaskRegulatoryBasis,
            name="tasks_regulatory_basis_enum",
            native_enum=True,
            create_type=False,
        ),
        nullable=False,
    )

    status = Column(
        SAEnum(
            TaskStatus,
            name="tasks_status_enum",
            native_enum=True,
            create_type=False,
        ),
        nullable=False,
    )

    # -------------------------------------------------
    # Assignment
    # -------------------------------------------------
    assigned_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
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
        SAEnum(
            CompletionReferenceType,
            name="tasks_completion_ref_enum",
            native_enum=True,
            create_type=False,
        ),
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
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )