"""create sfv_requirements

Revision ID: 84a63a08a99d
Revises: a00fd20fbd36
Create Date: 2026-06-26 03:00:59.199245

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "84a63a08a99d"
down_revision = "a00fd20fbd36"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sfv_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("trigger_source_type", sa.String(length=32), nullable=False),
        sa.Column("trigger_reference_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trigger_symptom_group", sa.String(length=16), nullable=False),
        sa.Column("trigger_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "completed_visit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("visits.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="OPEN"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint(
            "trigger_source_type IN ('INITIAL_RN_ICA', 'HUV1', 'HUV2')",
            name="ck_sfv_requirements_trigger_source_type",
        ),
        sa.CheckConstraint(
            "trigger_symptom_group IN ('PAIN', 'NON_PAIN', 'BOTH')",
            name="ck_sfv_requirements_trigger_symptom_group",
        ),
        sa.CheckConstraint(
            "status IN ('OPEN', 'COMPLETED', 'OVERDUE', 'CANCELLED')",
            name="ck_sfv_requirements_status",
        ),
    )

    op.create_index(
        "ix_sfv_requirements_patient",
        "sfv_requirements",
        ["patient_id"],
        unique=False,
    )

    op.create_index(
        "ix_sfv_requirements_open_due",
        "sfv_requirements",
        ["patient_id", "status", "due_at"],
        unique=False,
    )

    op.create_index(
        "uq_sfv_requirements_trigger_once",
        "sfv_requirements",
        ["patient_id", "trigger_source_type", "trigger_reference_id"],
        unique=True,
    )


def downgrade():
    op.drop_index("uq_sfv_requirements_trigger_once", table_name="sfv_requirements")
    op.drop_index("ix_sfv_requirements_open_due", table_name="sfv_requirements")
    op.drop_index("ix_sfv_requirements_patient", table_name="sfv_requirements")
    op.drop_table("sfv_requirements")