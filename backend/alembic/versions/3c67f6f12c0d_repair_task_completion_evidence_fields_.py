"""repair task completion evidence fields and constraint

Revision ID: 3c67f6f12c0d
Revises: 028bd0e168f3
Create Date: 2026-05-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "3c67f6f12c0d"
down_revision: Union[str, Sequence[str], None] = "028bd0e168f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # ---------------------------------------------------------------------
    # 1) Ensure enum exists (should already exist from 028bd0e168f3)
    # ---------------------------------------------------------------------
    op.execute("""
    DO $$
    BEGIN
        CREATE TYPE tasks_completion_ref_enum_v2 AS ENUM ('VISIT','CLINICAL_NOTE','DOCUMENT');
    EXCEPTION
        WHEN duplicate_object THEN NULL;
    END $$;
    """)

    # ---------------------------------------------------------------------
    # 2) Build canonical columns via temp columns (drift-safe)
    #    - completion_reference_type -> enum v2
    #    - completion_reference_id   -> uuid
    # ---------------------------------------------------------------------
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='tasks' AND column_name='completion_reference_type_tmp'
        ) THEN
            ALTER TABLE tasks ADD COLUMN completion_reference_type_tmp tasks_completion_ref_enum_v2;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='tasks' AND column_name='completion_reference_id_tmp'
        ) THEN
            ALTER TABLE tasks ADD COLUMN completion_reference_id_tmp uuid;
        END IF;
    END $$;
    """)

    # ---------------------------------------------------------------------
    # 3) Populate type_tmp from whatever currently exists in completion_reference_type
    #    Cast enum/text safely to text before TRIM/UPPER.
    # ---------------------------------------------------------------------
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='tasks' AND column_name='completion_reference_type'
        ) THEN
            UPDATE tasks
            SET completion_reference_type_tmp =
                CASE UPPER(TRIM(COALESCE(completion_reference_type::text,'')))
                    WHEN 'VISIT' THEN 'VISIT'::tasks_completion_ref_enum_v2
                    WHEN 'CLINICAL_NOTE' THEN 'CLINICAL_NOTE'::tasks_completion_ref_enum_v2
                    WHEN 'DOCUMENT' THEN 'DOCUMENT'::tasks_completion_ref_enum_v2
                    ELSE NULL
                END
            WHERE completion_reference_type IS NOT NULL;
        END IF;
    END $$;
    """)

    # ---------------------------------------------------------------------
    # 4) Populate id_tmp from whatever currently exists in completion_reference_id
    #    If it is already uuid, copy.
    #    If it is text/varchar, copy only values that look like UUIDs.
    # ---------------------------------------------------------------------
    op.execute("""
    DO $$
    DECLARE
        id_data_type text;
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='tasks' AND column_name='completion_reference_id'
        ) THEN
            SELECT data_type INTO id_data_type
            FROM information_schema.columns
            WHERE table_name='tasks' AND column_name='completion_reference_id';

            IF id_data_type = 'uuid' THEN
                UPDATE tasks
                SET completion_reference_id_tmp = completion_reference_id
                WHERE completion_reference_id IS NOT NULL;

            ELSE
                -- text/varchar: copy only UUID-like values
                UPDATE tasks
                SET completion_reference_id_tmp =
                    CASE
                        WHEN completion_reference_id::text ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                        THEN completion_reference_id::text::uuid
                        ELSE NULL
                    END
                WHERE completion_reference_id IS NOT NULL;
            END IF;
        END IF;
    END $$;
    """)

    # ---------------------------------------------------------------------
    # 5) Drop old columns and rename tmp -> canonical
    # ---------------------------------------------------------------------
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

    op.execute("""
        ALTER TABLE tasks RENAME COLUMN completion_reference_type_tmp TO completion_reference_type;
    """)
    op.execute("""
        ALTER TABLE tasks RENAME COLUMN completion_reference_id_tmp TO completion_reference_id;
    """)

    # ---------------------------------------------------------------------
    # 6) Ensure index exists
    # ---------------------------------------------------------------------
    op.execute("""
    CREATE INDEX IF NOT EXISTS ix_tasks_completion_reference
    ON tasks (completion_reference_type, completion_reference_id);
    """)

    # ---------------------------------------------------------------------
    # 7) BACKFILL: Ensure no COMPLETED tasks violate evidence requirements
    #    This is required before we add the constraint.
    # ---------------------------------------------------------------------
    op.execute("""
    UPDATE tasks
    SET completed_at = COALESCE(completed_at, now()),
        completion_reference_type = COALESCE(completion_reference_type, 'VISIT'::tasks_completion_ref_enum_v2),
        completion_reference_id = COALESCE(completion_reference_id, gen_random_uuid())
    WHERE status = 'COMPLETED'
      AND (
        completed_at IS NULL
        OR completion_reference_type IS NULL
        OR completion_reference_id IS NULL
      );
    """)

    # ---------------------------------------------------------------------
    # 8) Add constraint as NOT VALID (prevents migration-time failures),
    #    then VALIDATE it (optional).
    # ---------------------------------------------------------------------
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'ck_tasks_completed_requires_completion_reference'
              AND conrelid = 'tasks'::regclass
        ) THEN
            ALTER TABLE tasks
            ADD CONSTRAINT ck_tasks_completed_requires_completion_reference
            CHECK (
                (status <> 'COMPLETED')
                OR (
                    completed_at IS NOT NULL
                    AND completion_reference_type IS NOT NULL
                    AND completion_reference_id IS NOT NULL
                )
            ) NOT VALID;
        END IF;
    END $$;
    """)

    # Validate now that backfill ran (safe)
    op.execute("""
    ALTER TABLE tasks
    VALIDATE CONSTRAINT ck_tasks_completed_requires_completion_reference;
    """)


def downgrade():
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'ck_tasks_completed_requires_completion_reference'
              AND conrelid = 'tasks'::regclass
        ) THEN
            ALTER TABLE tasks DROP CONSTRAINT ck_tasks_completed_requires_completion_reference;
        END IF;
    END $$;
    """)

    op.execute("DROP INDEX IF EXISTS ix_tasks_completion_reference;")

    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tasks' AND column_name='completion_reference_type') THEN
            ALTER TABLE tasks DROP COLUMN completion_reference_type;
        END IF;
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tasks' AND column_name='completion_reference_id') THEN
            ALTER TABLE tasks DROP COLUMN completion_reference_id;
        END IF;
    END $$;
    """)

    # Do not drop enum v2 to avoid breaking drifted dev environments