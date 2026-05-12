"""Add task engine for HUV/SFV

Revision ID: b8699a65514c
Revises: efb85249ff6a
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID


revision = "b8699a65514c"
down_revision = "efb85249ff6a"
branch_labels = None
depends_on = "b677e343f59f"


# IMPORTANT:
# create_type=False prevents SQLAlchemy from auto-creating the enum
# during table creation (which is what caused the DuplicateObject error).
task_type_enum = postgresql.ENUM(
    "HUV", "SFV", "OTHER",
    name="tasks_task_type_enum",
    create_type=False,
)
origin_enum = postgresql.ENUM(
    "ADMISSION", "PERIODIC", "MANUAL",
    name="tasks_origin_enum",
    create_type=False,
)
discipline_enum = postgresql.ENUM(
    "RN", "MD", "NP", "SW", "CHAPLAIN", "AIDE",
    name="tasks_discipline_enum",
    create_type=False,
)
status_enum = postgresql.ENUM(
    "PENDING", "COMPLETED", "OVERDUE", "ESCALATED", "WAIVED",
    name="tasks_status_enum",
    create_type=False,
)
completion_ref_enum = postgresql.ENUM(
    "VISIT", "NOTE", "ORDER",
    name="tasks_completion_ref_enum",
    create_type=False,
)
reg_basis_enum = postgresql.ENUM(
    "IDG", "VISIT_FREQUENCY", "F2F", "CERTIFICATION", "ADMISSION_REQUIREMENT",
    name="tasks_regulatory_basis_enum",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()

    # Create enum types safely (only if missing)
    task_type_enum.create(bind, checkfirst=True)
    origin_enum.create(bind, checkfirst=True)
    discipline_enum.create(bind, checkfirst=True)
    status_enum.create(bind, checkfirst=True)
    completion_ref_enum.create(bind, checkfirst=True)
    reg_basis_enum.create(bind, checkfirst=True)

    # Create tasks table (enums will NOT auto-create because create_type=False)
    op.create_table(
        "tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),

        sa.Column("patient_id", UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),

        sa.Column(
            "benefit_period_id",
            UUID(as_uuid=True),
            sa.ForeignKey("benefit_periods.id"),
            nullable=False,
        ),

        sa.Column("task_type", task_type_enum, nullable=False),
        sa.Column("origin", origin_enum, nullable=False),
        sa.Column("discipline", discipline_enum, nullable=False),

        sa.Column("assigned_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),

        sa.Column("regulatory_basis", reg_basis_enum, nullable=False),

        sa.Column("due_date", sa.Date, nullable=False),

        sa.Column("status", status_enum, nullable=False, server_default=sa.text("'PENDING'")),

        sa.Column("completed_at", sa.DateTime, nullable=True),

        sa.Column("completion_reference_type", completion_ref_enum, nullable=True),
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
    bind = op.get_bind()

    op.drop_table("tasks")

    reg_basis_enum.drop(bind, checkfirst=True)
    completion_ref_enum.drop(bind, checkfirst=True)
    status_enum.drop(bind, checkfirst=True)
    discipline_enum.drop(bind, checkfirst=True)
    origin_enum.drop(bind, checkfirst=True)
    task_type_enum.drop(bind, checkfirst=True)