"""add audit fields to tasks

Revision ID: 2ba9efd2c832
Revises: aafe4439c4ee
Create Date: 2026-04-30 08:18:58.570022
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "2ba9efd2c832"
down_revision: Union[str, Sequence[str], None] = "aafe4439c4ee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    DO $$
    BEGIN
      IF to_regclass('public.tasks') IS NULL THEN
        RAISE EXCEPTION 'public.tasks does not exist; tasks creator migration was not applied';
      END IF;

      -- Make NOT NULL + defaults safe by only applying if column exists and isn’t already not-null.
      -- Ensure columns exist first:
      ALTER TABLE public.tasks
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now();

      ALTER TABLE public.tasks
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now();

      -- If you want strict NOT NULL, set it safely (will succeed if data exists)
      BEGIN
        ALTER TABLE public.tasks ALTER COLUMN created_at SET NOT NULL;
      EXCEPTION WHEN others THEN
        -- ignore if already not null or cannot be set yet
        NULL;
      END;

      BEGIN
        ALTER TABLE public.tasks ALTER COLUMN updated_at SET NOT NULL;
      EXCEPTION WHEN others THEN
        NULL;
      END;

    END $$;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_tasks_created_by", table_name="tasks")
    op.drop_column("tasks", "created_by")
    op.drop_column("tasks", "updated_at")
    op.drop_column("tasks", "created_at")
