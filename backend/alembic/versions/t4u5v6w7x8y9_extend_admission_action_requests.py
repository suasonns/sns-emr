"""extend admission_action_requests for DME/supplies/referral/physician-contact

Extends the existing Admission Action Center tracker (created in
q8r9s0t1u2v3) with the shared fields the DME, Supplies, Referral, and
Physician Contact workflows require: responsible discipline, priority,
required-by date, a flexible per-type `type_details` JSONB payload,
optional plan-of-care linkage, timestamped completion evidence, and a
cancellation reason. Also adds the CANCELED/IN_PROGRESS statuses and the
PHYSICIAN_CONTACT request type at the application layer (no DB-level enum
constraint existed before, so no enum migration is required).

Purely additive: new nullable/defaulted columns only. No existing column,
constraint, or data is modified.

Revision ID: t4u5v6w7x8y9
Revises: s3t4u5v6w7x8
Create Date: 2026-08-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "t4u5v6w7x8y9"
down_revision = "s3t4u5v6w7x8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "admission_action_requests",
        sa.Column("responsible_discipline", sa.String(32), nullable=True),
    )
    op.add_column(
        "admission_action_requests",
        sa.Column(
            "priority", sa.String(16), nullable=False, server_default=sa.text("'ROUTINE'")
        ),
    )
    op.add_column(
        "admission_action_requests",
        sa.Column("required_by_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "admission_action_requests",
        sa.Column(
            "type_details", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")
        ),
    )
    op.add_column(
        "admission_action_requests",
        sa.Column(
            "plan_of_care_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plan_of_care_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "admission_action_requests",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "admission_action_requests",
        sa.Column("completion_evidence", sa.Text(), nullable=True),
    )
    op.add_column(
        "admission_action_requests",
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_admission_action_requests_plan_of_care_version_id",
        "admission_action_requests",
        ["plan_of_care_version_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_admission_action_requests_plan_of_care_version_id",
        table_name="admission_action_requests",
    )
    op.drop_column("admission_action_requests", "cancellation_reason")
    op.drop_column("admission_action_requests", "completion_evidence")
    op.drop_column("admission_action_requests", "completed_at")
    op.drop_column("admission_action_requests", "plan_of_care_version_id")
    op.drop_column("admission_action_requests", "type_details")
    op.drop_column("admission_action_requests", "required_by_date")
    op.drop_column("admission_action_requests", "priority")
    op.drop_column("admission_action_requests", "responsible_discipline")
