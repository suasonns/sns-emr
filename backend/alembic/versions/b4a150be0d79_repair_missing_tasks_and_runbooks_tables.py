"""repair_missing_tasks_and_runbooks_tables

Revision ID: b4a150be0d79
Revises: cac211c9999e
Create Date: 2026-05-25 08:01:03.058035

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b4a150be0d79"
down_revision: Union[str, Sequence[str], None] = "cac211c9999e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # --- TASKS TABLE (CRITICAL) ---
    if "tasks" not in existing_tables:
        op.create_table(
            "tasks",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(), nullable=False),
            sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("visit_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("task_type", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("origin", sa.String(), nullable=False),
            sa.Column("due_date", sa.Date(), nullable=True),

            # completion evidence (NON‑NEGOTIABLE)
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("completion_reference_type", sa.String(), nullable=True),
            sa.Column("completion_reference_id", postgresql.UUID(as_uuid=True), nullable=True),

            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),

            sa.ForeignKeyConstraint(
                ["patient_id"], ["patients.id"], name="fk_tasks_patient"
            ),
            sa.ForeignKeyConstraint(
                ["visit_id"], ["visits.id"], name="fk_tasks_visit"
            ),
        )

        op.create_index("ix_tasks_tenant_id", "tasks", ["tenant_id"])
        op.create_index("ix_tasks_status", "tasks", ["status"])
        op.create_index("ix_tasks_task_type", "tasks", ["task_type"])

    # --- RUNBOOKS TABLE (COMPLIANCE SNAPSHOT) ---
    if "runbooks" not in existing_tables:
        op.create_table(
            "runbooks",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(), nullable=False),
            sa.Column("baseline_tag", sa.String(), nullable=False),
            sa.Column("generated_at", sa.DateTime(), nullable=False),

            # immutable compliance snapshot
            sa.Column("policy_snapshot", postgresql.JSONB(), nullable=False),

            sa.Column("created_at", sa.DateTime(), nullable=False),
        )

        op.create_index("ix_runbooks_tenant_id", "runbooks", ["tenant_id"])


def downgrade() -> None:
    # Repair migration — no downgrade by design
    pass