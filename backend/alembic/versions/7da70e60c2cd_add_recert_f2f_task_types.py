"""add recert and f2f task types

Revision ID: 7da70e60c2cd
Revises: c71945a19f0b
Create Date: 2026-05-01
"""

from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "7da70e60c2cd"
down_revision: Union[str, Sequence[str], None] = "c71945a19f0b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_enum
            WHERE enumlabel = 'CERTIFICATION'
              AND enumtypid = 'tasks_task_type_enum'::regtype
        ) THEN
            ALTER TYPE tasks_task_type_enum ADD VALUE 'CERTIFICATION';
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM pg_enum
            WHERE enumlabel = 'RECERTIFICATION'
              AND enumtypid = 'tasks_task_type_enum'::regtype
        ) THEN
            ALTER TYPE tasks_task_type_enum ADD VALUE 'RECERTIFICATION';
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM pg_enum
            WHERE enumlabel = 'F2F'
              AND enumtypid = 'tasks_task_type_enum'::regtype
        ) THEN
            ALTER TYPE tasks_task_type_enum ADD VALUE 'F2F';
        END IF;
    END$$;
    """)


def downgrade():
    # PostgreSQL enums are forward-only
    pass