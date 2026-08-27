"""add patient_issues table

Revision ID: 5d3e2a1b4c6d
Revises: ab93ea51d692
Create Date: 2026-08-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "5d3e2a1b4c6d"
down_revision = "ab93ea51d692"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patient_issues",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("identified_date", sa.Date(), nullable=False),
        sa.Column(
            "identified_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'OPEN'")),
        sa.Column("outcome_notes", sa.Text(), nullable=True),
        sa.Column("resolved_date", sa.Date(), nullable=True),
        sa.Column(
            "resolved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_patient_issues_tenant_id", "patient_issues", ["tenant_id"])
    op.create_index("ix_patient_issues_patient_id", "patient_issues", ["patient_id"])
    op.create_index("ix_patient_issues_status", "patient_issues", ["status"])
    op.create_index(
        "ix_patient_issues_tenant_patient_identified_date",
        "patient_issues",
        ["tenant_id", "patient_id", "identified_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_patient_issues_tenant_patient_identified_date", table_name="patient_issues")
    op.drop_index("ix_patient_issues_status", table_name="patient_issues")
    op.drop_index("ix_patient_issues_patient_id", table_name="patient_issues")
    op.drop_index("ix_patient_issues_tenant_id", table_name="patient_issues")
    op.drop_table("patient_issues")
