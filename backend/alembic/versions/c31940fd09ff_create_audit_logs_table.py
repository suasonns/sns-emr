"""create_audit_logs_table

Revision ID: c31940fd09ff
Revises: 75b96f0ac8c6
Create Date: 2026-05-31 10:45:57.229947

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ✅ CORRECT REVISION CHAIN (DO NOT CHANGE)
revision: str = "c31940fd09ff"
down_revision: Union[str, Sequence[str], None] = "75b96f0ac8c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """
    ✅ CREATE AUDIT LOG TABLE (IDEMPOTENT / SAFE)
    """

    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_name = 'audit_logs'
        ) THEN

            CREATE TABLE audit_logs (
                id UUID PRIMARY KEY,
                tenant_id UUID NOT NULL,
                request_id VARCHAR(128),
                ip_address VARCHAR(64),

                user_id UUID,
                role VARCHAR(64),

                action_type VARCHAR(64) NOT NULL,
                entity_type VARCHAR(64),
                entity_id UUID,

                description TEXT,
                event_metadata JSONB,

                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );

            -- ✅ INDEXES
            CREATE INDEX ix_audit_logs_tenant_id ON audit_logs (tenant_id);
            CREATE INDEX ix_audit_logs_user_id ON audit_logs (user_id);
            CREATE INDEX ix_audit_logs_action_type ON audit_logs (action_type);
            CREATE INDEX ix_audit_logs_entity_id ON audit_logs (entity_id);
            CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at);

        END IF;
    END$$;
    """)


def downgrade():
    """
    ⚠️ Optional (forward-only system)
    """

    op.execute("DROP TABLE IF EXISTS audit_logs;")