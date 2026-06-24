"""add clinical note completion reference type

Revision ID: a17db9b53221
Revises: 93a8694600a9
Create Date: 2026-06-17
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a17db9b53221"
down_revision: Union[str, Sequence[str], None] = "93a8694600a9"
branch_labels = None
depends_on = None


# ✅ CONFIG — MAKE SURE THESE MATCH YOUR DB
ENUM_TYPE_NAME = "tasks_completion_ref_enum_v2"
TABLE_NAME = "tasks"
COLUMN_NAME = "completion_reference_type"
CHECK_CONSTRAINT_NAME = "ck_tasks_completion_reference_type_allowed"


def upgrade() -> None:
    """
    ✅ Add CLINICAL_NOTE to enum and allow it in constraint
    """

    # ✅ STEP 1 — Add enum value safely (idempotent)
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid
                WHERE t.typname = '{ENUM_TYPE_NAME}'
                  AND e.enumlabel = 'CLINICAL_NOTE'
            ) THEN
                ALTER TYPE {ENUM_TYPE_NAME} ADD VALUE 'CLINICAL_NOTE';
            END IF;
        END
        $$;
        """
    )

    # ✅ STEP 2 — Drop existing constraint
    op.execute(
        f"""
        ALTER TABLE {TABLE_NAME}
        DROP CONSTRAINT IF EXISTS {CHECK_CONSTRAINT_NAME};
        """
    )

    # ✅ STEP 3 — Recreate constraint WITH CLINICAL_NOTE
    op.execute(
        f"""
        ALTER TABLE {TABLE_NAME}
        ADD CONSTRAINT {CHECK_CONSTRAINT_NAME}
        CHECK (
            {COLUMN_NAME} IS NULL
            OR {COLUMN_NAME}::text IN (
                'VISIT',
                'NOTE',
                'DOCUMENT',
                'CLINICAL_NOTE'
            )
        );
        """
    )


def downgrade() -> None:
    """
    ⚠️ Safe rollback (does NOT remove enum value)
    """

    # ✅ STEP 1 — Convert existing values back
    op.execute(
        f"""
        UPDATE {TABLE_NAME}
        SET {COLUMN_NAME} = 'VISIT'
        WHERE {COLUMN_NAME}::text = 'CLINICAL_NOTE';
        """
    )

    # ✅ STEP 2 — Drop constraint
    op.execute(
        f"""
        ALTER TABLE {TABLE_NAME}
        DROP CONSTRAINT IF EXISTS {CHECK_CONSTRAINT_NAME};
        """
    )

    # ✅ STEP 3 — Recreate WITHOUT CLINICAL_NOTE
    op.execute(
        f"""
        ALTER TABLE {TABLE_NAME}
        ADD CONSTRAINT {CHECK_CONSTRAINT_NAME}
        CHECK (
            {COLUMN_NAME} IS NULL
            OR {COLUMN_NAME}::text IN (
                'VISIT',
                'NOTE',
                'DOCUMENT'
            )
        );
        """
    )