"""add patient_assignments table

Revision ID: 3b236f1a012b
Revises: beea7b77395c
Create Date: 2026-05-26 16:43:36.956971

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3b236f1a012b'
down_revision: Union[str, Sequence[str], None] = 'beea7b77395c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    op.create_table(
        "patient_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),

        # RN / MSW / SC (extend later if needed)
        sa.Column("discipline", sa.String(length=16), nullable=False),

        # staff assignment (user id)
        sa.Column("staff_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),

        # geography routing (zip/region/zone string)
        sa.Column("service_area", sa.String(length=64), nullable=True),

        # assignment lifecycle
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'ASSIGNED'")),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),

        sa.Column("note", sa.Text(), nullable=True),
    )

    # prevent multiple active assignments per discipline per patient
    op.create_index(
        "ix_patient_assignments_active_unique",
        "patient_assignments",
        ["tenant_id", "patient_id", "discipline", "status"],
        unique=True,
    )

    op.create_index(
        "ix_patient_assignments_patient",
        "patient_assignments",
        ["patient_id"],
    )


def downgrade():
    op.drop_index("ix_patient_assignments_patient", table_name="patient_assignments")
    op.drop_index("ix_patient_assignments_active_unique", table_name="patient_assignments")
    op.drop_table("patient_assignments")