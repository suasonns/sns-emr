"""add patient allergies table

Revision ID: 6e4e89b3ed4b
Revises: 9b7f6c4a1d2e
Create Date: 2026-08-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "6e4e89b3ed4b"
down_revision: Union[str, Sequence[str], None] = "9b7f6c4a1d2e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patient_allergies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("allergen_text", sa.String(length=255), nullable=False),
        sa.Column("allergen_type", sa.String(length=32), nullable=False, server_default=sa.text("'DRUG'")),
        sa.Column("drug_class", sa.String(length=64), nullable=True),
        sa.Column("reaction_description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_patient_allergies_patient_id", "patient_allergies", ["patient_id"], unique=False)
    op.create_index("ix_patient_allergies_drug_class", "patient_allergies", ["drug_class"], unique=False)
    op.create_index("ix_patient_allergies_patient_active", "patient_allergies", ["patient_id", "active"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_patient_allergies_patient_active", table_name="patient_allergies")
    op.drop_index("ix_patient_allergies_drug_class", table_name="patient_allergies")
    op.drop_index("ix_patient_allergies_patient_id", table_name="patient_allergies")
    op.drop_table("patient_allergies")
