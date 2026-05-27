"""create tasks table

Revision ID: cac211c9999e
Revises: 26b58abf2620
Create Date: 2026-05-23 08:10:09.299624
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "cac211c9999e"
down_revision: Union[str, Sequence[str], None] = "26b58abf2620"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# -------------------------------------------------
# ENUM DEFINITIONS (PostgreSQL)
# -------------------------------------------------

task_status_enum = postgresql.ENUM(
    "OPEN",
    "OVERDUE",
    "COMPLETED",
    "CANCELLED",
    name="task_status_enum",
    create_type=False,
)

task_origin_enum = postgresql.ENUM(
    "RULE",
    "VISIT",
    "PERIODIC",
    "MANUAL",
    name="task_origin_enum",
    create_type=False,
)

task_type_enum = postgresql.ENUM(
    "POC_UPDATE",
    name="task_type_enum",
    create_type=False,
)

completion_reference_type_enum = postgresql.ENUM(
    "VISIT",
    "NOTE",
    name="completion_reference_type_enum",
    create_type=False,
)


def _table_exists(table: str) -> bool:
    conn = op.get_bind()
    return bool(
        conn.execute(
            sa.text("SELECT to_regclass(:tbl) IS NOT NULL"),
            {"tbl": f"public.{table}"},
        ).scalar()
    )


def upgrade() -> None:
    bind = op.get_bind()

    # Ensure enums exist (idempotent)
    task_status_enum.create(bind, checkfirst=True)
    task_origin_enum.create(bind, checkfirst=True)
    task_type_enum.create(bind, checkfirst=True)
    completion_reference_type_enum.create(bind, checkfirst=True)

    # ✅ Rebuild-safe: tasks might already exist in another branch
    if _table_exists("tasks"):
        return

    op.create_table(
        "tasks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_type", task_type_enum, nullable=False),
        sa.Column(
            "status",
            task_status_enum,
            nullable=False,
            server_default=sa.text("'OPEN'::task_status_enum"),
        ),
        sa.Column("origin", task_origin_enum, nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("completion_reference_type", completion_reference_type_enum),
        sa.Column("completion_reference_id", postgresql.UUID(as_uuid=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            name="fk_tasks_patient",
            ondelete="CASCADE",
        ),
        sa.Index("ix_tasks_tenant_id", "tenant_id"),
        sa.Index("ix_tasks_patient_id", "patient_id"),
        sa.Index("ix_tasks_status", "status"),
        sa.Index("ix_tasks_due_date", "due_date"),
        schema="public",
    )


def downgrade() -> None:
    # Dev-only rollback, guarded
    if _table_exists("tasks"):
        op.drop_table("tasks", schema="public")