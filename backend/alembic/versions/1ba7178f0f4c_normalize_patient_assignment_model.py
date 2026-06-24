"""normalize patient assignment model

Revision ID: 1ba7178f0f4c
Revises: d45cb3f73cac
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect


revision: str = "1ba7178f0f4c"
down_revision: Union[str, Sequence[str], None] = "d45cb3f73cac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # =====================================================
    # CHECK IF TABLE EXISTS
    # =====================================================
    tables = inspector.get_table_names()

    if "patient_assignments" not in tables:

        op.create_table(
            "patient_assignments",

            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),

            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),

            sa.Column(
                "discipline",
                postgresql.ENUM(name="assignment_discipline_enum", create_type=False),
                nullable=False
            ),

            sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("status", sa.String(length=16), nullable=False, server_default="ASSIGNED"),
            sa.Column("service_area", sa.String(length=64), nullable=True),

            sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),

            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
            sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["assigned_by"], ["users.id"]),

            sa.PrimaryKeyConstraint("id"),
        )

        # indexes
        op.create_index("ix_pa_patient_id", "patient_assignments", ["patient_id"])
        op.create_index("ix_pa_user_id", "patient_assignments", ["user_id"])
        op.create_index("ix_pa_tenant_id", "patient_assignments", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_pa_tenant_id", table_name="patient_assignments")
    op.drop_index("ix_pa_user_id", table_name="patient_assignments")
    op.drop_index("ix_pa_patient_id", table_name="patient_assignments")

    op.drop_table("patient_assignments")