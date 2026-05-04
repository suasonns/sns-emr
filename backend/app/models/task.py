from sqlalchemy import Column, String, Date, DateTime, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class Task(BaseModel):
    __tablename__ = "tasks"

    # --- Task classification ---
    task_type = Column(
        Enum(
            "HUV",
            "SFV",
            "OTHER",
            "POC_UPDATE",
            "IDG_REVIEW",
            "CERTIFICATION",
            "RECERTIFICATION",
            "F2F",

            # ✅ Optional: only keep these if they EXIST in the DB enum
            # If not yet in DB, add them via an Alembic migration first.
            "POC_NONCOMPLIANT_STRUCTURE",
            "POC_REVIEW_REQUIRED",
            "POC_OUT_OF_SCOPE_CARE",
            "POC_STALE_REVIEW",
            "POC_PHYSICIAN_REVIEW_REQUIRED",

            name="tasks_task_type_enum",
            create_type=False,
        ),
        nullable=False,
    )

    origin = Column(
        Enum(
            "ADMISSION",
            "PERIODIC",
            "MANUAL",
            name="tasks_origin_enum",
            create_type=False,
        ),
        nullable=False,
        default="PERIODIC",
    )

    # --- Core relationships ---
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)

    # ✅ DB allows this to be NULL in your environment, so keep nullable=True
    benefit_period_id = Column(
        UUID(as_uuid=True),
        ForeignKey("benefit_periods.id"),
        nullable=True,
        index=True,
    )

    # --- Responsibility ---
    discipline = Column(
        Enum(
            "RN",
            "MD",
            "NP",
            "SW",
            "CHAPLAIN",
            "AIDE",
            name="tasks_discipline_enum",
            create_type=False,
        ),
        nullable=False,
    )

    assigned_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # --- CMS / Regulatory justification ---
    regulatory_basis = Column(
        Enum(
            "IDG",
            "VISIT_FREQUENCY",
            "F2F",
            "CERTIFICATION",
            "ADMISSION_REQUIREMENT",
            "POC_UPDATE",
            name="tasks_regulatory_basis_enum",
            create_type=False,
        ),
        nullable=False,
    )

    # --- Lifecycle ---
    due_date = Column(Date, nullable=False)

    status = Column(
        Enum(
            "PENDING",
            "COMPLETED",
            "OVERDUE",
            "ESCALATED",
            "WAIVED",
            name="tasks_status_enum",
            create_type=False,
        ),
        nullable=False,
        default="PENDING",
    )

    completed_at = Column(DateTime, nullable=True)

    # --- Completion traceability ---
    completion_reference_type = Column(
        Enum(
            "VISIT",
            "NOTE",
            "ORDER",
            "IDG_MEETING",
            "CERTIFICATION",
            "F2F_ENCOUNTER",
            name="tasks_completion_ref_enum",
            create_type=False,
        ),
        nullable=True,
    )

    # ✅ IMPORTANT: DB column is character varying — keep String
    completion_reference_id = Column(String, nullable=True)


# --- Indexes ---
Index("idx_tasks_patient", Task.patient_id)
Index("idx_tasks_benefit_period", Task.benefit_period_id)
Index("idx_tasks_discipline", Task.discipline)
Index("idx_tasks_status", Task.status)
Index("idx_tasks_due_date", Task.due_date)
