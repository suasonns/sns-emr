"""add skin_impairments table (longitudinal skin impairment registry)

Revision ID: f3a9b2c7d1e4
Revises: r9ica4v5l6nk
Create Date: 2026-11-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f3a9b2c7d1e4"
down_revision = "r9ica4v5l6nk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skin_impairments",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("condition_type", sa.String(length=64), nullable=False),
        sa.Column(
            "present_as_pressure_injury",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("location", sa.String(length=128), nullable=True),
        sa.Column("laterality", sa.String(length=32), nullable=True),
        sa.Column("opened_date", sa.Date(), nullable=True),
        sa.Column(
            "opened_visit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("visits.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "opened_assessment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rnica_assessments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "opened_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("opened_by_discipline", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'New'")),
        sa.Column("current_stage", sa.String(length=64), nullable=True),
        sa.Column("current_treatment_summary", sa.Text(), nullable=True),
        sa.Column(
            "last_assessment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rnica_assessments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "last_assessment_visit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("visits.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("last_assessment_date", sa.Date(), nullable=True),
        sa.Column("resolved_date", sa.Date(), nullable=True),
        sa.Column(
            "resolved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resolved_by_discipline", sa.String(length=50), nullable=True),
        sa.Column("resolution_reason", sa.String(length=64), nullable=True),
        sa.Column("resolution_narrative", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_skin_impairments_tenant_id", "skin_impairments", ["tenant_id"])
    op.create_index("ix_skin_impairments_patient_id", "skin_impairments", ["patient_id"])
    op.create_index("ix_skin_impairments_status", "skin_impairments", ["status"])
    op.create_index(
        "ix_skin_impairments_tenant_patient_status",
        "skin_impairments",
        ["tenant_id", "patient_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_skin_impairments_tenant_patient_status", table_name="skin_impairments")
    op.drop_index("ix_skin_impairments_status", table_name="skin_impairments")
    op.drop_index("ix_skin_impairments_patient_id", table_name="skin_impairments")
    op.drop_index("ix_skin_impairments_tenant_id", table_name="skin_impairments")
    op.drop_table("skin_impairments")
