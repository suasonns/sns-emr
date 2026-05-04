"""create certifications table

Revision ID: 5cc577fb901e
Revises: 1751ca54c771
Create Date: 2026-05-01 09:41:35.101404
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# ✅ REQUIRED Alembic revision identifiers
revision: str = "5cc577fb901e"
down_revision: Union[str, Sequence[str], None] = "1751ca54c771"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "certifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "benefit_period_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("benefit_periods.id"),
            nullable=False,
            index=True,
        ),

        # INITIAL or RECERT
        sa.Column("cert_type", sa.String(), nullable=False),

        # clinician signature + effective date
        sa.Column("signed_at", sa.DateTime(), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),

        # MD or NP
        sa.Column("signed_by_role", sa.String(), nullable=False),
        sa.Column("signed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),

        sa.Column(
            "status",
            sa.String(),
            nullable=False,
            server_default="FINALIZED",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
    )


def downgrade():
    op.drop_table("certifications")