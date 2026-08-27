"""create rnica_amendments table

SECTION 12 -- Amendment Infrastructure: a distinct, timestamped,
attributable correction/addendum record attached to an already-locked
(signed) RN ICA assessment. Never overwrites the signed
`rnica_assessments.form_data`; approving an amendment only changes this
row's status/approved_by/approved_at, never the original record.

Additive migration only; does not modify any existing table or data.

Revision ID: r1s2t3u4v5w6
Revises: b35658e9dca5
Create Date: 2026-08-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "r1s2t3u4v5w6"
down_revision = "b35658e9dca5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rnica_amendments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "rnica_assessment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rnica_assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("section_reference", sa.String(128), nullable=True),
        sa.Column("amendment_category", sa.String(32), nullable=False),
        sa.Column("reason_code", sa.String(32), nullable=False),
        sa.Column("requested_change", sa.Text(), nullable=False),
        sa.Column("original_value_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("proposed_value", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("denied_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_rnica_amendments_tenant_id", "rnica_amendments", ["tenant_id"])
    op.create_index("ix_rnica_amendments_patient_id", "rnica_amendments", ["patient_id"])
    op.create_index("ix_rnica_amendments_rnica_assessment_id", "rnica_amendments", ["rnica_assessment_id"])
    op.create_index("ix_rnica_amendments_amendment_category", "rnica_amendments", ["amendment_category"])
    op.create_index("ix_rnica_amendments_status", "rnica_amendments", ["status"])
    op.create_index("ix_rnica_amendments_created_by", "rnica_amendments", ["created_by"])
    op.create_index(
        "ix_rnica_amendments_assessment_status",
        "rnica_amendments",
        ["rnica_assessment_id", "status"],
    )
    op.create_index(
        "ix_rnica_amendments_patient_status",
        "rnica_amendments",
        ["patient_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_rnica_amendments_patient_status", table_name="rnica_amendments")
    op.drop_index("ix_rnica_amendments_assessment_status", table_name="rnica_amendments")
    op.drop_index("ix_rnica_amendments_created_by", table_name="rnica_amendments")
    op.drop_index("ix_rnica_amendments_status", table_name="rnica_amendments")
    op.drop_index("ix_rnica_amendments_amendment_category", table_name="rnica_amendments")
    op.drop_index("ix_rnica_amendments_rnica_assessment_id", table_name="rnica_amendments")
    op.drop_index("ix_rnica_amendments_patient_id", table_name="rnica_amendments")
    op.drop_index("ix_rnica_amendments_tenant_id", table_name="rnica_amendments")
    op.drop_table("rnica_amendments")
