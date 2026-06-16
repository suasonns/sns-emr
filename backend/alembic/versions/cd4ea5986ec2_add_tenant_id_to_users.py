"""add_tenant_id_to_users (rebuild-safe)

Revision ID: cd4ea5986ec2
Revises: f5ee8cb51e19
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "cd4ea5986ec2"
down_revision = "f5ee8cb51e19"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)

    if "users" not in inspector.get_table_names():
        return

    columns = {c["name"] for c in inspector.get_columns("users")}

    # ✅ SAFE: only add column if missing
    if "tenant_id" not in columns:
        op.add_column(
            "users",
            sa.Column("tenant_id", sa.UUID(), nullable=True),
            schema="public",
        )

    # ✅ Refresh schema state
    inspector = inspect(conn)

    fk_names = {
        fk["name"]
        for fk in inspector.get_foreign_keys("users")
        if fk.get("name")
    }

    # ✅ SAFE FK
    if "tenants" in inspector.get_table_names():
        if "fk_users_tenant_id" not in fk_names:
            op.create_foreign_key(
                "fk_users_tenant_id",
                "users",
                "tenants",
                ["tenant_id"],
                ["id"],
                schema="public",
                referent_schema="public",
                ondelete="SET NULL",
            )

    # ✅ SAFE INDEX
    idx_names = {
        idx["name"]
        for idx in inspector.get_indexes("users")
    }

    if "ix_users_tenant_id" not in idx_names:
        op.create_index(
            "ix_users_tenant_id",
            "users",
            ["tenant_id"],
            unique=False,
        )


def downgrade():
    # ✅ Forward-only system (DO NOT DROP COLUMN)
    pass