"""add POC_UPDATE to tasks_task_type_enum

Revision ID: f58020cc5ea2
Revises: d3cc58c6ab3f
Create Date: 2026-04-30 16:54:55.548919

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f58020cc5ea2'
down_revision: Union[str, Sequence[str], None] = 'd3cc58c6ab3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade():
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM pg_enum e
            JOIN pg_type t ON t.oid = e.enumtypid
            WHERE t.typname = 'tasks_task_type_enum'
              AND e.enumlabel = 'POC_UPDATE'
        ) THEN
            ALTER TYPE tasks_task_type_enum ADD VALUE 'POC_UPDATE';
        END IF;
    END$$;
    """)


def downgrade():
    # PostgreSQL enums cannot safely remove values in a downgrade.
    pass

