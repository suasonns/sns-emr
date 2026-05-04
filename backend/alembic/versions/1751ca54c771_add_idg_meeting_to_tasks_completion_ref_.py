"""add IDG_MEETING to tasks_completion_ref_enum

Revision ID: 1751ca54c771
Revises: 5fb19c15af0b
Create Date: 2026-05-01 08:22:24.294687

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1751ca54c771'
down_revision: Union[str, Sequence[str], None] = '5fb19c15af0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from alembic import op

def upgrade():
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM pg_enum e
            JOIN pg_type t ON t.oid = e.enumtypid
            WHERE t.typname = 'tasks_completion_ref_enum'
              AND e.enumlabel = 'IDG_MEETING'
        ) THEN
            ALTER TYPE tasks_completion_ref_enum ADD VALUE 'IDG_MEETING';
        END IF;
    END$$;
    """)


def downgrade():
    pass
