"""add_commlog_acknowledgement_workflow

Revision ID: cd825533874b
Revises: aa20706258fd
Create Date: 2026-06-19 16:37:05.303006

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'cd825533874b'
down_revision: Union[str, Sequence[str], None] = 'aa20706258fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    DO $$
    BEGIN

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='communications_logs' AND column_name='status'
        ) THEN
            ALTER TABLE communications_logs
            ADD COLUMN status TEXT DEFAULT 'RECEIVED' NOT NULL;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='communications_logs' AND column_name='acknowledged_by'
        ) THEN
            ALTER TABLE communications_logs ADD COLUMN acknowledged_by UUID;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='communications_logs' AND column_name='acknowledged_at'
        ) THEN
            ALTER TABLE communications_logs ADD COLUMN acknowledged_at TIMESTAMPTZ;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='communications_logs' AND column_name='verified_by'
        ) THEN
            ALTER TABLE communications_logs ADD COLUMN verified_by UUID;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='communications_logs' AND column_name='verified_at'
        ) THEN
            ALTER TABLE communications_logs ADD COLUMN verified_at TIMESTAMPTZ;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='communications_logs' AND column_name='resolved_by'
        ) THEN
            ALTER TABLE communications_logs ADD COLUMN resolved_by UUID;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='communications_logs' AND column_name='resolved_at'
        ) THEN
            ALTER TABLE communications_logs ADD COLUMN resolved_at TIMESTAMPTZ;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE table_name='communications_logs'
              AND constraint_name='ck_communications_logs_status_allowed'
        ) THEN
            ALTER TABLE communications_logs
            ADD CONSTRAINT ck_communications_logs_status_allowed
            CHECK (status IN ('RECEIVED', 'ACKNOWLEDGED', 'VERIFIED', 'RESOLVED'));
        END IF;

    END
    $$;
    """)