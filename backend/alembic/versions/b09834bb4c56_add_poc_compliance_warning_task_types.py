"""add POC compliance warning task types

Revision ID: b09834bb4c56
Revises: a02609edbe7d
Create Date: 2026-05-02 12:49:34.040445
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b09834bb4c56"
down_revision = "a02609edbe7d"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    DO $$
    DECLARE
        v_type text;
    BEGIN
        -- find the enum type used by tasks.task_type
        SELECT t.typname INTO v_type
        FROM pg_attribute a
        JOIN pg_class c ON c.oid = a.attrelid
        JOIN pg_type t ON t.oid = a.atttypid
        WHERE c.relname = 'tasks'
          AND a.attname = 'task_type'
          AND a.attnum > 0
          AND NOT a.attisdropped;

        -- Add enum values only if missing
        IF NOT EXISTS (
            SELECT 1 FROM pg_enum e JOIN pg_type tt ON tt.oid = e.enumtypid
            WHERE tt.typname = v_type AND e.enumlabel = 'POC_NONCOMPLIANT_STRUCTURE'
        ) THEN EXECUTE format('ALTER TYPE %I ADD VALUE %L', v_type, 'POC_NONCOMPLIANT_STRUCTURE'); END IF;

        IF NOT EXISTS (
            SELECT 1 FROM pg_enum e JOIN pg_type tt ON tt.oid = e.enumtypid
            WHERE tt.typname = v_type AND e.enumlabel = 'POC_REVIEW_REQUIRED'
        ) THEN EXECUTE format('ALTER TYPE %I ADD VALUE %L', v_type, 'POC_REVIEW_REQUIRED'); END IF;

        IF NOT EXISTS (
            SELECT 1 FROM pg_enum e JOIN pg_type tt ON tt.oid = e.enumtypid
            WHERE tt.typname = v_type AND e.enumlabel = 'POC_OUT_OF_SCOPE_CARE'
        ) THEN EXECUTE format('ALTER TYPE %I ADD VALUE %L', v_type, 'POC_OUT_OF_SCOPE_CARE'); END IF;

        IF NOT EXISTS (
            SELECT 1 FROM pg_enum e JOIN pg_type tt ON tt.oid = e.enumtypid
            WHERE tt.typname = v_type AND e.enumlabel = 'POC_STALE_REVIEW'
        ) THEN EXECUTE format('ALTER TYPE %I ADD VALUE %L', v_type, 'POC_STALE_REVIEW'); END IF;

        IF NOT EXISTS (
            SELECT 1 FROM pg_enum e JOIN pg_type tt ON tt.oid = e.enumtypid
            WHERE tt.typname = v_type AND e.enumlabel = 'POC_PHYSICIAN_REVIEW_REQUIRED'
        ) THEN EXECUTE format('ALTER TYPE %I ADD VALUE %L', v_type, 'POC_PHYSICIAN_REVIEW_REQUIRED'); END IF;
    END $$;
    """)


def downgrade():
    # forward-only enum change
    pass