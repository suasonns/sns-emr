"""add bereavement_letter_trackers

Revision ID: 7b2f4e9a1c6d
Revises: 5d1c9a3e7f2b
Create Date: 2026-08-25 16:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "7b2f4e9a1c6d"
down_revision = "5d1c9a3e7f2b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bereavement_letter_trackers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "bereavement_poc_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("bereavement_pocs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "bereavement_assessment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("bereavement_assessments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("date_of_death", sa.Date(), nullable=True),
        sa.Column("risk_level", sa.String(length=16), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="ACTIVE"),
        sa.Column("discontinued_reason", sa.Text(), nullable=True),
        sa.Column("discontinued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "discontinued_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("items", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_bereavement_letter_trackers_tenant_id",
        "bereavement_letter_trackers",
        ["tenant_id"],
    )
    op.create_index(
        "ix_bereavement_letter_trackers_patient_id",
        "bereavement_letter_trackers",
        ["patient_id"],
    )
    op.create_index(
        "ix_bereavement_letter_trackers_bereavement_poc_id",
        "bereavement_letter_trackers",
        ["bereavement_poc_id"],
    )
    op.create_index(
        "ix_bereavement_letter_trackers_bereavement_assessment_id",
        "bereavement_letter_trackers",
        ["bereavement_assessment_id"],
    )
    op.create_index(
        "ix_bereavement_letter_trackers_status",
        "bereavement_letter_trackers",
        ["status"],
    )
    # Supports the tenant-wide alerts query (WHERE tenant_id = ? AND status
    # = 'ACTIVE') efficiently as the table grows.
    op.create_index(
        "ix_bereavement_letter_trackers_tenant_status",
        "bereavement_letter_trackers",
        ["tenant_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_bereavement_letter_trackers_tenant_status", table_name="bereavement_letter_trackers")
    op.drop_index("ix_bereavement_letter_trackers_status", table_name="bereavement_letter_trackers")
    op.drop_index("ix_bereavement_letter_trackers_bereavement_assessment_id", table_name="bereavement_letter_trackers")
    op.drop_index("ix_bereavement_letter_trackers_bereavement_poc_id", table_name="bereavement_letter_trackers")
    op.drop_index("ix_bereavement_letter_trackers_patient_id", table_name="bereavement_letter_trackers")
    op.drop_index("ix_bereavement_letter_trackers_tenant_id", table_name="bereavement_letter_trackers")
    op.drop_table("bereavement_letter_trackers")
