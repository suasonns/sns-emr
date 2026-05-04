"""repair_add_idg_signatures

Revision ID: 8aabf0c30144
Revises: 5415a8ee619c
Create Date: 2026-05-04 09:39:49.676898
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8aabf0c30144'
down_revision: Union[str, Sequence[str], None] = '5415a8ee619c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    bind = op.get_bind()

    # ---- ENUM (safe, idempotent) ----
    idg_discipline = postgresql.ENUM(
        "RN",
        "MD",
        "MSW",
        "SC",
        "LVN",
        "NP",
        name="idg_discipline",
        create_type=False,
    )
    idg_discipline.create(bind, checkfirst=True)

    # ---- CREATE idg_signatures IF MISSING ----
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS idg_signatures (
            id UUID PRIMARY KEY,
            idg_review_id UUID NOT NULL
                REFERENCES idg_reviews(id)
                ON DELETE CASCADE,
            discipline idg_discipline NOT NULL,
            user_id UUID,
            signed_at TIMESTAMPTZ NOT NULL,
            CONSTRAINT uq_idg_signature_per_discipline
                UNIQUE (idg_review_id, discipline)
        );
        """
    )


def downgrade():
    pass