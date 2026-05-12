"""Create tasks table (minimal)

Revision ID: 4c586d69e593
Revises: 3a88b97a921b
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "4c586d69e593"
down_revision = "3a88b97a921b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # If tasks already exists (it will, via b8699a65514c), do nothing.
    # If tasks doesn't exist, create a minimal placeholder to allow later migrations
    # to run (dev repair safety).
    op.execute("""
    DO $$
    BEGIN
      IF to_regclass('public.tasks') IS NULL THEN
        CREATE TABLE tasks (
          id UUID PRIMARY KEY,
          patient_id UUID NOT NULL REFERENCES patients(id),
          status VARCHAR NOT NULL
        );
      END IF;
    END $$;
    """)

def downgrade():
    op.drop_table("tasks")