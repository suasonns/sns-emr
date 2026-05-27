"""
Create safety_assessments table

Revision ID: 0cf459de52f2
Revises: 104cd74a907d
Create Date: 2026-05-26 10:12:29
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# Alembic revision identifiers
revision: str = "0cf459de52f2"
down_revision: Union[str, Sequence[str], None] = "104cd74a907d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create the safety_assessments table.

    This table is the base for safety, fall risk, and environmental
    assessments and is extended by later migrations.
    """

    op.create_table(
        "safety_assessments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "data_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),

        # Audit / evidence fields
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signed_by", postgresql.UUID(as_uuid=True), nullable=True),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_safety_assessments_patient_id",
        "safety_assessments",
        ["patient_id"],
    )


def downgrade() -> None:
    """
    Downgrade drops the safety_assessments table.

    This downgrade is acceptable because the table is new and contains
    no irreversible ENUM dependencies.
    """
    op.drop_index(
        "ix_safety_assessments_patient_id",
        table_name="safety_assessments",
    )
    op.drop_table("safety_assessments")