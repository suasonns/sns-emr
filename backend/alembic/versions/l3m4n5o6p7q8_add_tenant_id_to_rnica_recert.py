"""add tenant_id to rnica_assessments and rn_recert_assessments (defense-in-depth)

Schema-only change: adds a nullable tenant_id column to both tables and
backfills it via a metadata-only join to patients.tenant_id. Does not read,
modify, or touch any clinical content (form_data, notes, scores, etc.) on
any existing row.

Revision ID: l3m4n5o6p7q8
Revises: k2l3m4n5o6p7
Create Date: 2026-08-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "l3m4n5o6p7q8"
down_revision = "k2l3m4n5o6p7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "rnica_assessments",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_rnica_assessments_tenant_id_tenants",
        "rnica_assessments",
        "tenants",
        ["tenant_id"],
        ["id"],
    )
    op.create_index(
        "ix_rnica_assessments_tenant_id",
        "rnica_assessments",
        ["tenant_id"],
    )
    op.execute(
        """
        UPDATE rnica_assessments AS r
        SET tenant_id = p.tenant_id
        FROM patients AS p
        WHERE r.patient_id = p.id
          AND r.tenant_id IS NULL
        """
    )

    op.add_column(
        "rn_recert_assessments",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_rn_recert_assessments_tenant_id_tenants",
        "rn_recert_assessments",
        "tenants",
        ["tenant_id"],
        ["id"],
    )
    op.create_index(
        "ix_rn_recert_assessments_tenant_id",
        "rn_recert_assessments",
        ["tenant_id"],
    )
    op.execute(
        """
        UPDATE rn_recert_assessments AS r
        SET tenant_id = p.tenant_id
        FROM patients AS p
        WHERE r.patient_id = p.id
          AND r.tenant_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_rn_recert_assessments_tenant_id", table_name="rn_recert_assessments")
    op.drop_constraint(
        "fk_rn_recert_assessments_tenant_id_tenants",
        "rn_recert_assessments",
        type_="foreignkey",
    )
    op.drop_column("rn_recert_assessments", "tenant_id")

    op.drop_index("ix_rnica_assessments_tenant_id", table_name="rnica_assessments")
    op.drop_constraint(
        "fk_rnica_assessments_tenant_id_tenants",
        "rnica_assessments",
        type_="foreignkey",
    )
    op.drop_column("rnica_assessments", "tenant_id")
