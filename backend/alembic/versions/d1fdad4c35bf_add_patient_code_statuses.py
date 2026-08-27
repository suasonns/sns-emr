"""add patient code statuses table

Revision ID: d1fdad4c35bf
Revises: q1r2s3t4u5v6
Create Date: 2026-08-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d1fdad4c35bf"
down_revision: Union[str, Sequence[str], None] = "q1r2s3t4u5v6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patient_code_statuses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code_status", sa.String(length=64), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("source", sa.String(length=64), nullable=False, server_default=sa.text("'FACESHEET'")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_patient_code_statuses_patient_id",
        "patient_code_statuses",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "ix_patient_code_statuses_patient_current",
        "patient_code_statuses",
        ["patient_id", "is_current"],
        unique=False,
    )
    op.create_index(
        "ix_patient_code_statuses_patient_effective",
        "patient_code_statuses",
        ["patient_id", "effective_date"],
        unique=False,
    )
    # Exactly one current row per patient.
    op.create_index(
        "uq_patient_code_statuses_one_current",
        "patient_code_statuses",
        ["patient_id"],
        unique=True,
        postgresql_where=sa.text("is_current = true"),
    )


def downgrade() -> None:
    op.drop_index("uq_patient_code_statuses_one_current", table_name="patient_code_statuses")
    op.drop_index("ix_patient_code_statuses_patient_effective", table_name="patient_code_statuses")
    op.drop_index("ix_patient_code_statuses_patient_current", table_name="patient_code_statuses")
    op.drop_index("ix_patient_code_statuses_patient_id", table_name="patient_code_statuses")
    op.drop_table("patient_code_statuses")
