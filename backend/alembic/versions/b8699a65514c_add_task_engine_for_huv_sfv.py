"""Add task engine for HUV/SFV

Revision ID: b8699a65514c
Revises: efb85249ff6a
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "b8699a65514c"
down_revision = "efb85249ff6a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- ENUM TYPES ---
    op.execute(
        "CREATE TYPE tasks_task_type_enum AS ENUM ('HUV', 'SFV', 'OTHER');"
    )
    op.execute(
        "CREATE TYPE tasks_origin_enum AS ENUM ('ADMISSION', 'PERIODIC', 'MANUAL');"
    )
    op.execute(
        "CREATE TYPE tasks_discipline_enum AS ENUM ('RN', 'MD', 'NP', 'SW', 'CHAPLAIN', 'AIDE');"
    )
    op.execute(
        "CREATE TYPE tasks_status_enum AS ENUM ('PENDING', 'COMPLETED', 'OVERDUE', 'ESCALATED', 'WAIVED');"
    )
    op.execute(
        "CREATE TYPE tasks_completion_ref_enum AS ENUM ('VISIT', 'NOTE', 'ORDER');"
    )
    op.execute(
        "CREATE TYPE tasks_regulatory_basis_enum "
        "AS ENUM ('IDG', 'VISIT_FREQUENCY', 'F2F', 'CERTIFICATION', 'ADMISSION_REQUIREMENT');"
    )

    # --- TASKS TABLE ---
    op.create_table(
        "tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("benefit_period_id", UUID(as_uuid=True), nullable=False),
        sa.Column("task_type", sa.Enum(name="tasks_task_type_enum"), nullable=False),
        sa.Column("origin", sa.Enum(name="tasks_origin_enum"), nullable=False),
        sa.Column("discipline", sa.Enum(name="tasks_discipline_enum"), nullable=False),
        sa.Column("assigned_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("regulatory_basis", sa.Enum(name="tasks_regulatory_basis_enum"), nullable=False),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("status", sa.Enum(name="tasks_status_enum"), nullable=False, server_default="PENDING"),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column(
            "completion_reference_type",
            sa.Enum(name="tasks_completion_ref_enum"),
            nullable=True,
        ),
        sa.Column("completion_reference_id", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    )

    op.create_index("idx_tasks_patient", "tasks", ["patient_id"])
    op.create_index("idx_tasks_benefit_period", "tasks", ["benefit_period_id"])
    op.create_index("idx_tasks_due_date", "tasks", ["due_date"])
    op.create_index("idx_tasks_status", "tasks", ["status"])


def downgrade() -> None:
    op.drop_table("tasks")

    op.execute("DROP TYPE tasks_regulatory_basis_enum;")
