"""Add compliance fields to tasks

Revision ID: 50a4ef7d9c9d
Revises: 4c586d69e593
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# Alembic revision identifiers
revision = "50a4ef7d9c9d"
down_revision = "4c586d69e593"
branch_labels = None
depends_on = None


def _create_enum_if_not_exists(enum_name: str, values: list[str]) -> None:
    """
    Creates a PostgreSQL ENUM type if it doesn't already exist.
    Safe to run multiple times.
    """
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


def upgrade():
    # --- ensure enum types exist (because tasks table started as minimal) ---
    _create_enum_if_not_exists("tasks_task_type_enum", ["HUV", "SFV", "OTHER"])
    _create_enum_if_not_exists("tasks_discipline_enum", ["RN", "MD", "NP", "SW", "CHAPLAIN", "AIDE"])
    _create_enum_if_not_exists("tasks_origin_enum", ["ADMISSION", "PERIODIC", "MANUAL"])
    _create_enum_if_not_exists("tasks_status_enum", ["PENDING", "COMPLETED", "OVERDUE", "ESCALATED", "WAIVED"])
    _create_enum_if_not_exists("tasks_completion_ref_enum", ["VISIT", "NOTE", "ORDER"])
    _create_enum_if_not_exists(
        "tasks_regulatory_basis_enum",
        ["IDG", "VISIT_FREQUENCY", "F2F", "CERTIFICATION", "ADMISSION_REQUIREMENT"],
    )

    # --- add columns ---
    op.add_column(
        "tasks",
        sa.Column("task_type", sa.Enum(name="tasks_task_type_enum"), nullable=True),
    )

    op.add_column(
        "tasks",
        sa.Column("discipline", sa.Enum(name="tasks_discipline_enum"), nullable=True),
    )

    op.add_column(
        "tasks",
        sa.Column("origin", sa.Enum(name="tasks_origin_enum"), nullable=True),
    )

    op.add_column(
        "tasks",
        sa.Column("due_date", sa.Date, nullable=True),
    )

    op.add_column(
        "tasks",
        sa.Column("assigned_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    )

    op.add_column(
        "tasks",
        sa.Column("benefit_period_id", UUID(as_uuid=True), nullable=True),
    )

    op.add_column(
        "tasks",
        sa.Column("regulatory_basis", sa.Enum(name="tasks_regulatory_basis_enum"), nullable=True),
    )

    op.add_column(
        "tasks",
        sa.Column("completion_reference_type", sa.Enum(name="tasks_completion_ref_enum"), nullable=True),
    )

    op.add_column(
        "tasks",
        sa.Column("completion_reference_id", sa.String, nullable=True),
    )


def downgrade():
    op.drop_column("tasks", "completion_reference_id")
    op.drop_column("tasks", "completion_reference_type")
    op.drop_column("tasks", "regulatory_basis")
    op.drop_column("tasks", "benefit_period_id")
    op.drop_column("tasks", "assigned_user_id")
    op.drop_column("tasks", "due_date")
    op.drop_column("tasks", "origin")
    op.drop_column("tasks", "discipline")
    op.drop_column("tasks", "task_type")