"""
add_rnica_assessment_table

Revision ID: 0b73f1e255db
Revises: fe1386604aff
Create Date: 2026-08-13 01:45:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0b73f1e255db"
down_revision: Union[str, Sequence[str], None] = "fe1386604aff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rnica_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("visit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assessment_type", sa.String(length=32), nullable=False, server_default="RNICA"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="DRAFT"),
        sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("form_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_rnica_assessments_patient_id"), "rnica_assessments", ["patient_id"], unique=False)
    op.create_index(op.f("ix_rnica_assessments_visit_id"), "rnica_assessments", ["visit_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_rnica_assessments_visit_id"), table_name="rnica_assessments")
    op.drop_index(op.f("ix_rnica_assessments_patient_id"), table_name="rnica_assessments")
    op.drop_table("rnica_assessments")
