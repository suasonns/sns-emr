"""create chha_pocs table

Revision ID: 282649a795c2
Revises: a607d41d5f51
Create Date: 2026-05-02 08:52:05.466033

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '282649a795c2'
down_revision: Union[str, Sequence[str], None] = 'a607d41d5f51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "chha_pocs",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "patient_id",
            UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
        ),

        # lifecycle
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),

        # effective window
        sa.Column("effective_start", sa.Date(), nullable=True),
        sa.Column("effective_end", sa.Date(), nullable=True),

        # RN-directed aide plan content
        sa.Column("frequency", sa.String(), nullable=True),          # e.g. "3x/week"
        sa.Column("adl_scope", sa.Text(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("safety_precautions", sa.Text(), nullable=True),

        # RN sign-off
        sa.Column("finalized_at", sa.DateTime(), nullable=True),
        sa.Column(
            "finalized_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),

        # audit
        sa.Column(
            "created_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.execute("CREATE INDEX IF NOT EXISTS ix_chha_pocs_patient_id ON chha_pocs(patient_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_chha_pocs_status ON chha_pocs(status);")


def downgrade():
    op.drop_table("chha_pocs")