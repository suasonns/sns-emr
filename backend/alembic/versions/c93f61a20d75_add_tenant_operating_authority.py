"""add tenant operating authority (ein, ptan)

An agency can be onboarded before it holds Medicare credentials, but it cannot
bill without them, so billing_enabled is constrained rather than the tenant
record itself.

Revision ID: c93f61a20d75
Revises: b1d4c7a90e11
Create Date: 2026-08-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c93f61a20d75"
down_revision: Union[str, Sequence[str], None] = "b1d4c7a90e11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("ein", sa.String(length=10), nullable=True))
    op.add_column("tenants", sa.Column("ptan", sa.String(length=32), nullable=True))

    op.create_index("ix_tenants_ein", "tenants", ["ein"])
    op.create_index("ix_tenants_ptan", "tenants", ["ptan"])

    op.create_check_constraint(
        "ck_tenant_ein_length",
        "tenants",
        "ein IS NULL OR char_length(ein) = 9",
    )

    # Existing tenants predate these fields, so any that are flagged billable
    # without credentials are stood down before the rule is enforced.
    op.execute(
        """
        UPDATE tenants
        SET billing_enabled = false
        WHERE billing_enabled = true
          AND (ein IS NULL OR ptan IS NULL)
        """
    )

    op.create_check_constraint(
        "ck_tenant_billing_requires_operating_authority",
        "tenants",
        "billing_enabled = false OR (ein IS NOT NULL AND ptan IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_tenant_billing_requires_operating_authority",
        "tenants",
        type_="check",
    )
    op.drop_constraint("ck_tenant_ein_length", "tenants", type_="check")
    op.drop_index("ix_tenants_ptan", table_name="tenants")
    op.drop_index("ix_tenants_ein", table_name="tenants")
    op.drop_column("tenants", "ptan")
    op.drop_column("tenants", "ein")
