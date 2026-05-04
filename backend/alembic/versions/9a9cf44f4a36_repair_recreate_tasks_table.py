"""repair recreate tasks table

Revision ID: 9a9cf44f4a36
Revises: eb851de9e5e1
Create Date: 2026-04-30 13:48:45.744796
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import ENUM


# revision identifiers, used by Alembic.
revision: str = "9a9cf44f4a36"
down_revision: Union[str, Sequence[str], None] = "eb851de9e5e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_enum_if_not_exists(enum_name: str, values: list[str]) -> None:
    values_sql = ", ".join([f"'{v}'" for v in values])
    op.execute(
        f"""
        DO $$
        BEGIN
            CREATE TYPE {enum_name} AS ENUM ({values_sql});
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )


def upgrade() -> None:
    conn = op.get_bind()

    exists = conn.execute(sa.text("""
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema='public' AND table_name='tasks'
        LIMIT 1
    """)).scalar()

    if exists:
        return

    # --- Ensure enum types exist ---
    _create_enum_if_not_exists("tasks_task_type_enum", ["HUV", "SFV", "OTHER"])
    _create_enum_if_not_exists("tasks_origin_enum", ["ADMISSION", "PERIODIC", "MANUAL"])
    _create_enum_if_not_exists("tasks_discipline_enum", ["RN", "LVN", "MD", "NP", "SW", "CHAPLAIN", "AIDE"])
    _create_enum_if_not_exists("tasks_status_enum", ["PENDING", "COMPLETED", "OVERDUE", "ESCALATED", "WAIVED"])
    _create_enum_if_not_exists("tasks_completion_ref_enum", ["VISIT", "NOTE", "ORDER"])
    _create_enum_if_not_exists(
        "tasks_regulatory_basis_enum",
        ["IDG", "VISIT_FREQUENCY", "F2F", "CERTIFICATION", "ADMISSION_REQUIREMENT"],
    )

   # --- Create tasks table ---
    op.create_table(
        "tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),

        sa.Column(
            "patient_id",
            UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),

        sa.Column(
            "benefit_period_id",
            UUID(as_uuid=True),
            sa.ForeignKey("benefit_periods.id"),
            nullable=True,
        ),

        sa.Column(
            "task_type",
            ENUM(name="tasks_task_type_enum", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "origin",
            ENUM(name="tasks_origin_enum", create_type=False),
            nullable=False,
            server_default="PERIODIC",
        ),
        sa.Column(
            "discipline",
            ENUM(name="tasks_discipline_enum", create_type=False),
            nullable=False,
        ),

        sa.Column(
            "assigned_user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),

        sa.Column(
            "regulatory_basis",
            ENUM(name="tasks_regulatory_basis_enum", create_type=False),
            nullable=False,
            server_default="VISIT_FREQUENCY",
        ),

        sa.Column("due_date", sa.Date, nullable=False),

        sa.Column(
            "status",
            ENUM(name="tasks_status_enum", create_type=False),
            nullable=False,
            server_default="PENDING",
        ),

        sa.Column("completed_at", sa.DateTime, nullable=True),

        sa.Column(
            "completion_reference_type",
            ENUM(name="tasks_completion_ref_enum", create_type=False),
            nullable=True,
        ),
        sa.Column("completion_reference_id", sa.String, nullable=True),

        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    )

    op.create_index("idx_tasks_patient", "tasks", ["patient_id"])
    op.create_index("idx_tasks_due_date", "tasks", ["due_date"])
    op.create_index("idx_tasks_status", "tasks", ["status"])
    op.create_index("idx_tasks_discipline", "tasks", ["discipline"])
    op.create_index("idx_tasks_benefit_period", "tasks", ["benefit_period_id"])


def downgrade() -> None:
    # Repair migrations should not drop critical tables automatically.
    pass
