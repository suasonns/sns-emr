"""add_tenant_id_to_patients (rebuild-safe)

Revision ID: 60a0912e0f06
Revises: cd4ea5986ec2
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "60a0912e0f06"
down_revision = "cd4ea5986ec2"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)

    if "patients" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("patients")}

    # ✅ SAFE COLUMN ADD
    if "tenant_id" not in columns:
        op.add_column(
            "patients",
            sa.Column("tenant_id", sa.UUID(), nullable=True),
            schema="public",
        )

    # ✅ Refresh schema after column change
    inspector = inspect(conn)

    # ✅ SAFE FK
    fk_names = {
        fk["name"]
        for fk in inspector.get_foreign_keys("patients")
        if fk.get("name")
    }

    if "tenants" in inspector.get_table_names():
        if "fk_patients_tenant_id" not in fk_names:
            op.create_foreign_key(
                "fk_patients_tenant_id",
                "patients",
                "tenants",
                ["tenant_id"],
                ["id"],
                source_schema="public",
                referent_schema="public",
                ondelete="SET NULL",
            )

    # ✅ SAFE INDEX
    indexes = {
        idx["name"]
        for idx in inspector.get_indexes("patients")
    }

    if "ix_patients_tenant_id" not in indexes:
        op.create_index(
            "ix_patients_tenant_id",
            "patients",
            ["tenant_id"],
            unique=False,
        )


def downgrade():
    # ✅ forward-only — never drop tenant_id
    pass