"""add IDG_REVIEW to tasks_task_type_enum

Revision ID: d8e10b78f236
Revises: f58020cc5ea2
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "d8e10b78f236"
down_revision = "f58020cc5ea2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL requires enum ADD VALUE to be committed
    # before it can be referenced in indexes or constraints
    with op.get_context().autocommit_block():
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


def downgrade() -> None:
    # Enum values cannot be safely removed
    pass