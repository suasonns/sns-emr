"""
notifications table

Revision ID: f8994c89ffb3
Revises: fdee78f61832
Create Date: 2026-06-03 17:31:42.907402
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# ---------------------------------------------------------
# Alembic identifiers
# ---------------------------------------------------------

revision: str = "f8994c89ffb3"
down_revision: Union[str, Sequence[str], None] = "fdee78f61832"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------
# Upgrade
# ---------------------------------------------------------

def upgrade() -> None:
    bind = op.get_bind()

    tenant_rows = bind.execute(
        text("SELECT schema_name FROM core.tenants WHERE schema_name IS NOT NULL")
    ).fetchall()

    for (schema_name,) in tenant_rows:
        bind.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS {schema_name}.notifications (
                    id uuid PRIMARY KEY,
                    user_id uuid NOT NULL,
                    patient_id uuid NOT NULL,
                    source_type text NOT NULL,
                    source_id uuid NOT NULL,
                    message text NOT NULL,
                    created_at timestamptz NOT NULL DEFAULT now(),
                    seen_at timestamptz NULL
                );
                """
            )
        )

        bind.execute(
            text(
                f"""
                CREATE INDEX IF NOT EXISTS ix_notifications_user
                ON {schema_name}.notifications (user_id, created_at DESC);
                """
            )
        )


# ---------------------------------------------------------
# Downgrade (blocked by design)
# ---------------------------------------------------------

def downgrade() -> None:
    raise RuntimeError("Downgrade not permitted for notifications baseline")
