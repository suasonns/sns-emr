"""add task completion evidence reference fields

Revision ID: 028bd0e168f3
Revises: 10eebc0d9587
Create Date: 2026-05-05 11:12:29.306661
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "028bd0e168f3"
down_revision: Union[str, Sequence[str], None] = "10eebc0d9587"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # ------------------------------------------------------------
    # 1) Create enum type used for completion evidence references
    #    NOTE: We create a v2 enum to avoid Postgres "unsafe new enum value" issues.
    # ------------------------------------------------------------
    op.execute("""
    DO $$
    BEGIN
        CREATE TYPE tasks_completion_ref_enum_v2 AS ENUM ('VISIT','CLINICAL_NOTE','DOCUMENT');
    EXCEPTION
        WHEN duplicate_object THEN NULL;
    END $$;
    """)

    # ------------------------------------------------------------
    # 2) Add evidence columns to tasks (drift-safe / idempotent)
    #    completion_reference_type: enum
    #    completion_reference_id: uuid (canonical target type)
    # ------------------------------------------------------------
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='tasks' AND column_name='completion_reference_type'
        ) THEN
            ALTER TABLE tasks
            ADD COLUMN completion_reference_type tasks_completion_ref_enum_v2;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='tasks' AND column_name='completion_reference_id'
        ) THEN
            ALTER TABLE tasks
            ADD COLUMN completion_reference_id uuid;
        END IF;
    END $$;
    """)

    # ------------------------------------------------------------
    # 3) Index for reporting/audit queries (drift-safe)
    # ------------------------------------------------------------
    op.execute("""
    CREATE INDEX IF NOT EXISTS ix_tasks_completion_reference
    ON tasks (completion_reference_type, completion_reference_id);
    """)

    # ------------------------------------------------------------
    # IMPORTANT:
    # We DO NOT add the check constraint here.
    # The constraint must be added AFTER the repair/backfill migration (3c67f6f12c0d),
    # otherwise Postgres will block the repair UPDATEs.
    # ------------------------------------------------------------


def downgrade():
    # Drop index if exists
    op.execute("DROP INDEX IF EXISTS ix_tasks_completion_reference;")

    # Drop columns if exist (drift-safe)
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='tasks' AND column_name='completion_reference_type'
        ) THEN
            ALTER TABLE tasks DROP COLUMN completion_reference_type;
        END IF;

        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='tasks' AND column_name='completion_reference_id'
        ) THEN
            ALTER TABLE tasks DROP COLUMN completion_reference_id;
        END IF;
    END $$;
    """)

    # NOTE: We intentionally do not drop the enum type tasks_completion_ref_enum_v2
    # because other migrations may depend on it in a drifted dev environment.