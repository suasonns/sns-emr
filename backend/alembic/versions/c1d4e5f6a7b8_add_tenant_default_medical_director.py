"""add tenants.default_medical_director_physician_id

Revision ID: c1d4e5f6a7b8
Revises: b7c3d2e1f0a9
Create Date: 2026-09-04 14:00:00.000000

The hospice Medical Director is an agency governance decision, never a
value hospital documents determine or that HNP harvesting should ever
populate. This adds a nullable FK on `tenants` pointing at a record in
that SAME tenant's own `physicians` directory (tenant-scoped -- never
another tenant's physician, never a platform/seed record). When unset,
the agency has not configured a default and the UI must show
NOT_CONFIGURED rather than falling back to any other value.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c1d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b7c3d2e1f0a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Composite-FK safety net: a plain FK on physicians.id alone cannot stop
    # a tenant's default pointing at ANOTHER tenant's physician row -- only
    # a composite FK against (tenant_id, id) can. physicians.id is already
    # globally unique (UUID PK), so this unique constraint is a no-op on
    # existing data and exists purely to give the composite FK below
    # something to reference.
    op.create_unique_constraint(
        "uq_physicians_tenant_id_id",
        "physicians",
        ["tenant_id", "id"],
    )

    op.add_column(
        "tenants",
        sa.Column(
            "default_medical_director_physician_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_tenants_default_medical_director_physician_id",
        "tenants",
        "physicians",
        # tenants.id is the tenant's own PK -- a physician's
        # default_medical_director assignment is only valid if that
        # physician's tenant_id equals THIS tenant's id.
        ["id", "default_medical_director_physician_id"],
        ["tenant_id", "id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_tenants_default_medical_director_physician_id",
        "tenants",
        ["default_medical_director_physician_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tenants_default_medical_director_physician_id",
        table_name="tenants",
    )
    op.drop_constraint(
        "fk_tenants_default_medical_director_physician_id",
        "tenants",
        type_="foreignkey",
    )
    op.drop_column("tenants", "default_medical_director_physician_id")
    op.drop_constraint(
        "uq_physicians_tenant_id_id",
        "physicians",
        type_="unique",
    )
