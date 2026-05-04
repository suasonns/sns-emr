"""add IDG_REVIEW to tasks_task_type_enum

Revision ID: 5fb19c15af0b
Revises: bb6f01ef3d84
Create Date: 2026-05-01 08:15:19.296901

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5fb19c15af0b'
down_revision: Union[str, Sequence[str], None] = 'bb6f01ef3d84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM pg_enum
            WHERE enumlabel = 'IDG_REVIEW'
              AND enumtypid = (
                  SELECT oid FROM pg_type WHERE typname = 'tasks_task_type_enum'
              )
        ) THEN
            ALTER TYPE tasks_task_type_enum ADD VALUE 'IDG_REVIEW';
        END IF;
    END$$;
    """)

def downgrade():
    # PostgreSQL enums cannot safely remove values
    pass