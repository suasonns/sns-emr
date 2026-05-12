"""create interface scoped rbac

Revision ID: d6039fa93bd2
Revises: 82b2a9fbc4c7
Create Date: 2026-05-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# -------------------------------------------------------------------
# Alembic revision identifiers
# -------------------------------------------------------------------
revision: str = "d6039fa93bd2"
down_revision: Union[str, Sequence[str], None] = "82b2a9fbc4c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# -------------------------------------------------------------------
# Upgrade
# -------------------------------------------------------------------
def upgrade():
    # -------------------------------------------------------------
    # Roles (scoped to an interface)
    # -------------------------------------------------------------
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("interface_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.UniqueConstraint(
            "interface_id",
            "name",
            name="uq_roles_interface_name",
        ),
    )

    op.create_foreign_key(
        "fk_roles_interface",
        "roles",
        "interfaces",
        ["interface_id"],
        ["id"],
    )

    # -------------------------------------------------------------
    # User + Interface + Role (time-bound grants)
    # -------------------------------------------------------------
    op.create_table(
        "user_interface_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interface_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "assigned_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "revoked_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_uir_tenant",
        "user_interface_roles",
        "tenants",
        ["tenant_id"],
        ["id"],
    )

    op.create_foreign_key(
        "fk_uir_user",
        "user_interface_roles",
        "users",
        ["user_id"],
        ["id"],
    )

    op.create_foreign_key(
        "fk_uir_interface",
        "user_interface_roles",
        "interfaces",
        ["interface_id"],
        ["id"],
    )

    op.create_foreign_key(
        "fk_uir_role",
        "user_interface_roles",
        "roles",
        ["role_id"],
        ["id"],
    )

# -------------------------------------------------------------------
# Downgrade (included for completeness only)
# -------------------------------------------------------------------
def downgrade():
    op.drop_table("user_interface_roles")
    op.drop_table("roles")
