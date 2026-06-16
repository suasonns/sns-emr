"""
communications log tables

Revision ID: fdee78f61832
Revises: 6f7963234886
Create Date: 2026-06-03 16:15:22.024058
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# ----------------------------------------------------------------------
# Alembic revision identifiers
# ----------------------------------------------------------------------

revision: str = "fdee78f61832"
down_revision: Union[str, Sequence[str], None] = "6f7963234886"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------

ALLOWED_EVENT_TYPES = (
    "MD_ORDER_CLARIFICATION",
    "CHANGE_OF_CONDITION",
    "FALL",
    "INCIDENT",
    "COMPLAINT",
    "MISSED_VISIT",
    "RESCHEDULED_VISIT",
    "AFTER_HOURS_CALL",
    "OFFICE_CALL",
    "DPCS_INSTRUCTION",
    "RN_AVAILABILITY",
    "LVN_AVAILABILITY",
    "UPDATE_SENT_TO_RN",
    "UPDATE_SENT_TO_MD",
)


def _safe_schema_name(name: str) -> bool:
    """
    Allow only schema names containing letters, digits, underscore.
    Prevents SQL injection via schema_name.
    """
    if not name:
        return False
    return name.replace("_", "").isalnum()


def upgrade() -> None:
    """
    Creates tenant-scoped communications log tables in each tenant schema.

    Forward-only baseline:
    - {tenant_schema}.communications_logs
    - {tenant_schema}.communications_log_attachments
    """

    bind = op.get_bind()

    tenant_rows = bind.execute(
        text("SELECT schema_name FROM core.tenants WHERE schema_name IS NOT NULL")
    ).fetchall()

    for (schema_name,) in tenant_rows:
        if not _safe_schema_name(schema_name):
            continue

        # 1) communications_logs
        bind.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS {schema_name}.communications_logs (
                    id uuid PRIMARY KEY,
                    patient_id uuid NOT NULL,
                    event_type text NOT NULL,
                    event_time timestamptz NOT NULL DEFAULT now(),
                    direction text NULL,
                    subject text NULL,
                    summary text NOT NULL,
                    details jsonb NULL,
                    created_by uuid NULL,
                    created_at timestamptz NOT NULL DEFAULT now(),
                    amended_from_id uuid NULL,
                    amended_reason text NULL,
                    amended_at timestamptz NULL
                );
                """
            )
        )

        # 2) event_type constraint (idempotent)
        allowed = ",".join([f"'{v}'" for v in ALLOWED_EVENT_TYPES])
        bind.execute(
            text(
                f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_constraint
                        WHERE conname = 'ck_communications_logs_event_type'
                          AND conrelid = '{schema_name}.communications_logs'::regclass
                    ) THEN
                        ALTER TABLE {schema_name}.communications_logs
                        ADD CONSTRAINT ck_communications_logs_event_type
                        CHECK (event_type IN ({allowed}));
                    END IF;
                END $$;
                """
            )
        )

        # 3) indexes (idempotent)
        bind.execute(
            text(
                f"""
                CREATE INDEX IF NOT EXISTS ix_commlog_patient_time
                ON {schema_name}.communications_logs (patient_id, event_time DESC);
                """
            )
        )
        bind.execute(
            text(
                f"""
                CREATE INDEX IF NOT EXISTS ix_commlog_event_type
                ON {schema_name}.communications_logs (event_type);
                """
            )
        )

        # 4) attachments table (metadata only; file bytes stored elsewhere)
        bind.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS {schema_name}.communications_log_attachments (
                    id uuid PRIMARY KEY,
                    log_id uuid NOT NULL,
                    file_name text NOT NULL,
                    file_path text NOT NULL,
                    content_type text NULL,
                    sha256 text NULL,
                    uploaded_by uuid NULL,
                    uploaded_at timestamptz NOT NULL DEFAULT now(),
                    CONSTRAINT fk_commlog_attachment_log
                        FOREIGN KEY (log_id)
                        REFERENCES {schema_name}.communications_logs(id)
                        ON DELETE CASCADE
                );
                """
            )
        )

        bind.execute(
            text(
                f"""
                CREATE INDEX IF NOT EXISTS ix_commlog_attach_log
                ON {schema_name}.communications_log_attachments (log_id);
                """
            )
        )


def downgrade() -> None:
    """
    Downgrade intentionally blocked (compliance baseline).
    """
    raise RuntimeError("Downgrade not permitted for communications log baseline")