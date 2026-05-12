"""add tenant_id to core tables

Revision ID: 82b2a9fbc4c7
Revises: fd22b6945770
Create Date: 2026-05-07 09:28:30.669916
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# -------------------------------------------------------------------
# Alembic revision identifiers
# -------------------------------------------------------------------
revision: str = "82b2a9fbc4c7"
down_revision: Union[str, Sequence[str], None] = "fd22b6945770"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# -------------------------------------------------------------------
# Default tenant (already created in Step 2)
# -------------------------------------------------------------------
DEFAULT_TENANT_ID = "0dac0f4a-9ce2-470d-8c1d-1c4e210b560d"

# -------------------------------------------------------------------
# Wave 1 core tables ONLY (must exist)
# -------------------------------------------------------------------
TABLES = [
    "users",
    "patients",
    "visits",
    "clinical_notes",
    "medications",
    "benefit_periods",
    "tasks",
]

# -------------------------------------------------------------------
# Upgrade
# -------------------------------------------------------------------
def upgrade():
    # ---------------------------------------------------------
    # 1. Add tenant_id as NULLABLE
    # ---------------------------------------------------------
    for table in TABLES:
        op.add_column(
            table,
            sa.Column(
                "tenant_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,
            ),
        )

    # ---------------------------------------------------------
    # 2. Backfill tenant_id using default tenant
    # (Alembic op.execute takes ONE argument only)
    # ---------------------------------------------------------
    for table in TABLES:
        op.execute(
            f"""
            UPDATE {table}
            SET tenant_id = '{DEFAULT_TENANT_ID}'
            WHERE tenant_id IS NULL
            """
        )

    # ---------------------------------------------------------
    # 3. Enforce NOT NULL + foreign key constraint
    # ---------------------------------------------------------
    for table in TABLES:
        op.alter_column(
            table,
            "tenant_id",
            nullable=False,
        )
        op.create_foreign_key(
            f"fk_{table}_tenant",
            table,
            "tenants",
            ["tenant_id"],
            ["id"],
        )

# -------------------------------------------------------------------
# Downgrade (included for completeness only)
# -------------------------------------------------------------------
def downgrade():
    for table in TABLES:
        op.drop_constraint(
            f"fk_{table}_tenant",
            table,
            type_="foreignkey",
        )
        op.drop_column(table, "tenant_id")
