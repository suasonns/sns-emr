"""add POC_UPDATE to tasks_task_type_enum

Revision ID: f58020cc5ea2
Revises: d3cc58c6ab3f
Create Date: 2026-04-30 16:54:55.548919
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "f58020cc5ea2"
down_revision = "d3cc58c6ab3f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # IMPORTANT:
    # PostgreSQL requires enum ADD VALUE to be committed before it can be used
    # in subsequent DDL (e.g., partial indexes with WHERE task_type='POC_UPDATE').
    with op.get_context().autocommit_block():
        # Postgres 13 doesn't support ADD VALUE IF NOT EXISTS in all builds,
        # so we keep the existence check in a DO block.
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


def downgrade() -> None:
    # PostgreSQL enums cannot safely remove values in a downgrade.
    pass