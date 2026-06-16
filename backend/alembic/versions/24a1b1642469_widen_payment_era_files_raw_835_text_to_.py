"""
widen payment_era_files raw_835_text to TEXT (ENTERPRISE REBUILD-SAFE)

Revision ID: 24a1b1642469
Revises: afca53283f52
Create Date: 2026-06-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "24a1b1642469"
down_revision: Union[str, Sequence[str], None] = "afca53283f52"
branch_labels = None
depends_on = None


# -----------------------------------------------------
# helpers
# -----------------------------------------------------

def _schema_exists(bind, schema_name: str) -> bool:
    sql = sa.text(
        """
        SELECT 1
        FROM information_schema.schemata
        WHERE schema_name = :schema_name
        """
    )
    return bind.execute(sql, {"schema_name": schema_name}).first() is not None


def _table_exists(bind, schema: str, table: str) -> bool:
    sql = sa.text(
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = :schema
          AND table_name = :table
        """
    )
    return bind.execute(
        sql, {"schema": schema, "table": table}
    ).first() is not None


# -----------------------------------------------------
# upgrade
# -----------------------------------------------------

def upgrade() -> None:
    bind = op.get_bind()

    tenant_schema = "tenant_love_and_faith"

    # ✅ TENANT SCHEMA SAFE EXECUTION
    if _schema_exists(bind, tenant_schema):
        if _table_exists(bind, tenant_schema, "payment_era_files"):
            op.execute(
                sa.text(
                    f"""
                    ALTER TABLE {tenant_schema}.payment_era_files
                    ALTER COLUMN raw_835_text TYPE TEXT
                    """
                )
            )

    # ✅ PUBLIC SCHEMA (ALWAYS EXISTS)
    if _table_exists(bind, "public", "payment_era_files"):
        op.execute(
            """
            ALTER TABLE public.payment_era_files
            ALTER COLUMN raw_835_text TYPE TEXT
            """
        )


# -----------------------------------------------------
# downgrade
# -----------------------------------------------------

def downgrade() -> None:
    raise RuntimeError("Downgrade not permitted for audit payload widening")