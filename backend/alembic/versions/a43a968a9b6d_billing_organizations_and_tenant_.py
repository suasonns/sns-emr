"""
billing organizations and tenant billing link

Revision ID: a43a968a9b6d
Revises: 24a1b1642469
Create Date: 2026-06-03 13:06:05.841961
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ----------------------------------------------------------------------
# Alembic revision identifiers
# ----------------------------------------------------------------------

revision: str = "a43a968a9b6d"
down_revision: Union[str, Sequence[str], None] = "24a1b1642469"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ----------------------------------------------------------------------
# Canonical Billing Organization IDs
# ----------------------------------------------------------------------

NE_BILLING_ID = "00000000-0000-0000-0000-632455464000"


# ----------------------------------------------------------------------
# Upgrade
# ----------------------------------------------------------------------

def upgrade() -> None:
    """
    Create billing organizations and link tenants to a billing organization.
    Forward-only, enterprise-safe migration.
    """

    # ------------------------------------------------------------------
    # 1) Create billing_organizations (CORE metadata, non-clinical)
    # ------------------------------------------------------------------

    op.create_table(
        "billing_organizations",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "capability_tier",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.CheckConstraint(
            "capability_tier IN ('AUTOMATED', 'MANUAL')",
            name="ck_billing_org_capability_tier",
        ),
        sa.UniqueConstraint(
            "name",
            name="billing_organizations_name_unique",
        ),
        schema="core",
    )

    # ------------------------------------------------------------------
    # 2) Add billing_organization_id to core.tenants
    # ------------------------------------------------------------------

    op.add_column(
        "tenants",
        sa.Column(
            "billing_organization_id",
            sa.UUID(as_uuid=False),
            nullable=True,
        ),
        schema="core",
    )

    op.create_foreign_key(
        "fk_tenants_billing_organization",
        source_table="tenants",
        referent_table="billing_organizations",
        local_cols=["billing_organization_id"],
        remote_cols=["id"],
        source_schema="core",
        referent_schema="core",
        ondelete="SET NULL",
    )

    # ------------------------------------------------------------------
    # 3) Seed NE Billing as the only AUTOMATED billing organization
    # ------------------------------------------------------------------

    op.execute(
        sa.text(
            """
            INSERT INTO core.billing_organizations (id, name, capability_tier, active)
            VALUES (:id, :name, 'AUTOMATED', true)
            ON CONFLICT (id) DO NOTHING
            """
        ).bindparams(
            id=NE_BILLING_ID,
            name="NE Billing",
        )
    )


# ----------------------------------------------------------------------
# Downgrade
# ----------------------------------------------------------------------

def downgrade() -> None:
    """
    Downgrade is intentionally blocked.

    Billing organizations are system-level metadata.
    Removing them would break tenant configuration and audit history.
    """
    raise RuntimeError(
        "Downgrade not permitted for billing organization baseline migration"
    )
