"""add cert and f2f completion refs

Revision ID: 1f74a6ffb06f
Revises: 7da70e60c2cd
Create Date: 2026-05-01
"""

from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "1f74a6ffb06f"
down_revision: Union[str, Sequence[str], None] = "7da70e60c2cd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_enum
            WHERE enumlabel = 'CERTIFICATION'
              AND enumtypid = 'tasks_completion_ref_enum'::regtype
        ) THEN
            ALTER TYPE tasks_completion_ref_enum ADD VALUE 'CERTIFICATION';
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM pg_enum
            WHERE enumlabel = 'F2F_ENCOUNTER'
              AND enumtypid = 'tasks_completion_ref_enum'::regtype
        ) THEN
            ALTER TYPE tasks_completion_ref_enum ADD VALUE 'F2F_ENCOUNTER';
        END IF;
    END$$;
    """)


def downgrade():
    # PostgreSQL enums are forward-only
    pass