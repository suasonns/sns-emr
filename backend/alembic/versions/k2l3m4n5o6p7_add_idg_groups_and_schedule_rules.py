"""add idg_groups, idg_group_schedule_rules, patients.idg_group_id

Revision ID: k2l3m4n5o6p7
Revises: j1k2l3m4n5o6
Create Date: 2026-08-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "k2l3m4n5o6p7"
down_revision = "j1k2l3m4n5o6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "idg_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_idg_groups_tenant_name"),
    )
    op.create_index("ix_idg_groups_tenant_id", "idg_groups", ["tenant_id"])
    op.create_index("ix_idg_groups_is_active", "idg_groups", ["is_active"])

    op.create_table(
        "idg_group_schedule_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("idg_group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("nth_occurrences", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["idg_group_id"], ["idg_groups.id"]),
    )
    op.create_index("ix_idg_group_schedule_rules_tenant_id", "idg_group_schedule_rules", ["tenant_id"])
    op.create_index("ix_idg_group_schedule_rules_idg_group_id", "idg_group_schedule_rules", ["idg_group_id"])
    op.create_index("ix_idg_group_schedule_rules_is_active", "idg_group_schedule_rules", ["is_active"])

    op.add_column(
        "patients",
        sa.Column("idg_group_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_patients_idg_group_id", "patients", ["idg_group_id"])
    op.create_foreign_key(
        "fk_patients_idg_group_id",
        "patients",
        "idg_groups",
        ["idg_group_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_patients_idg_group_id", "patients", type_="foreignkey")
    op.drop_index("ix_patients_idg_group_id", table_name="patients")
    op.drop_column("patients", "idg_group_id")

    op.drop_index("ix_idg_group_schedule_rules_is_active", table_name="idg_group_schedule_rules")
    op.drop_index("ix_idg_group_schedule_rules_idg_group_id", table_name="idg_group_schedule_rules")
    op.drop_index("ix_idg_group_schedule_rules_tenant_id", table_name="idg_group_schedule_rules")
    op.drop_table("idg_group_schedule_rules")

    op.drop_index("ix_idg_groups_is_active", table_name="idg_groups")
    op.drop_index("ix_idg_groups_tenant_id", table_name="idg_groups")
    op.drop_table("idg_groups")
