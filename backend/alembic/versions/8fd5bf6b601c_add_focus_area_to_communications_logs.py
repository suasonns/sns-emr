"""
add focus_area to communications_logs

Revision ID: 8fd5bf6b601c
Revises: f8994c89ffb3
Create Date: 2026-06-03 17:56:08.272953

Forward-only repair migration:
- Adds focus_area column to tenant-scoped communications_logs tables
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# ---------------------------------------------------------
# Alembic identifiers
# ---------------------------------------------------------

revision: str = "8fd5bf6b601c"
down_revision: Union[str, Sequence[str], None] = "f8994c89ffb3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _safe_schema_name(name: str) -> bool:
    if not name:
        return False
    return name.replace("_", "").isalnum()


# ---------------------------------------------------------
# Upgrade
# ---------------------------------------------------------

def upgrade() -> None:
    bind = op.get_bind()

    tenant_rows = bind.execute(
        text("SELECT schema_name FROM core.tenants WHERE schema_name IS NOT NULL")
    ).fetchall()

    for (schema_name,) in tenant_rows:
        if not _safe_schema_name(schema_name):
            continue

        bind.execute(
            text(
                f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = '{schema_name}'
                          AND table_name = 'communications_logs'
                          AND column_name = 'focus_area'
                    ) THEN
                        ALTER TABLE {schema_name}.communications_logs
                        ADD COLUMN focus_area text NULL;
                    END IF;
                END $$;
                """
            )
        )


# ---------------------------------------------------------
# Downgrade (blocked by design)
# ---------------------------------------------------------

def downgrade() -> None:
    raise RuntimeError("Downgrade not permitted for focus_area repair migration")
