"""
update communications_logs event_type constraint

Revision ID: fe1386604aff
Revises: 8fd5bf6b601c
Create Date: 2026-06-03 18:18:19.322934

Forward-only repair:
- Expands allowed event_type values to match operational Communications Log usage
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = "fe1386604aff"
down_revision: Union[str, Sequence[str], None] = "8fd5bf6b601c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ALLOWED_EVENT_TYPES = (
    # Operational/UI types
    "Bereavement Note",
    "Check Status",
    "Comm Note",
    "On-Call Note",
    "Patient Notification",
    "Phone Call",
    "Progress Note",
    "Reminder",
    "Vol Note",

    # Keep legacy/system types for backward compatibility
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
    if not name:
        return False
    return name.replace("_", "").isalnum()


def upgrade() -> None:
    bind = op.get_bind()

    tenant_rows = bind.execute(
        text("SELECT schema_name FROM core.tenants WHERE schema_name IS NOT NULL")
    ).fetchall()

    allowed = ",".join([f"'{v}'" for v in ALLOWED_EVENT_TYPES])

    for (schema_name,) in tenant_rows:
        if not _safe_schema_name(schema_name):
            continue

        bind.execute(
            text(
                f"""
                ALTER TABLE {schema_name}.communications_logs
                DROP CONSTRAINT IF EXISTS ck_communications_logs_event_type;
                """
            )
        )

        bind.execute(
            text(
                f"""
                ALTER TABLE {schema_name}.communications_logs
                ADD CONSTRAINT ck_communications_logs_event_type
                CHECK (event_type IN ({allowed}));
                """
            )
        )


def downgrade() -> None:
    raise RuntimeError("Downgrade not permitted for communications_logs constraint repair")