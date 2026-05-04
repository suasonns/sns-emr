"""add IDG_REVIEW to tasks_task_type_enum

Revision ID: d8e10b78f236
Revises: f58020cc5ea2
Create Date: 2026-05-01 05:27:23.545458
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d8e10b78f236"
down_revision: Union[str, Sequence[str], None] = "f58020cc5ea2"
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
              AND e.enumlabel = 'IDG_REVIEW'
        ) THEN
            ALTER TYPE tasks_task_type_enum ADD VALUE 'IDG_REVIEW';
        END IF;
    END$$;
    """)


def downgrade():
    # PostgreSQL enums cannot safely remove values.
    # This migration is intentionally irreversible.
    pass