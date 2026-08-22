"""create admission_action_requests table

Admission Action Center (Phase A): a lightweight, dedicated request/status
tracker (Medication Request / Physician Order / DME Order / Supply Order /
Referral) reachable from every RN ICA section without navigating away from
the assessment. Deliberately simple lifecycle
(REQUESTED -> ORDERED -> SENT -> ACKNOWLEDGED -> DELIVERED -> COMPLETED)
with no approval routing and no fulfillment workflow -- those remain the
domain of `physician_orders` / `patient_orders` respectively.

Additive migration only; does not modify any existing table or data.

Revision ID: q8r9s0t1u2v3
Revises: p7q8r9s0t1u2
Create Date: 2026-08-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "q8r9s0t1u2v3"
down_revision = "p7q8r9s0t1u2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admission_action_requests",
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
            sa.ForeignKey("rnica_assessments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source_section", sa.String(64), nullable=True),
        sa.Column("request_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'REQUESTED'")),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("status_history", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_admission_action_requests_tenant_id", "admission_action_requests", ["tenant_id"])
    op.create_index("ix_admission_action_requests_patient_id", "admission_action_requests", ["patient_id"])
    op.create_index("ix_admission_action_requests_rnica_assessment_id", "admission_action_requests", ["rnica_assessment_id"])
    op.create_index("ix_admission_action_requests_request_type", "admission_action_requests", ["request_type"])
    op.create_index("ix_admission_action_requests_status", "admission_action_requests", ["status"])
    op.create_index("ix_admission_action_requests_created_by", "admission_action_requests", ["created_by"])
    op.create_index(
        "ix_admission_action_requests_patient_status",
        "admission_action_requests",
        ["patient_id", "status"],
    )
    op.create_index(
        "ix_admission_action_requests_patient_type",
        "admission_action_requests",
        ["patient_id", "request_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_admission_action_requests_patient_type", table_name="admission_action_requests")
    op.drop_index("ix_admission_action_requests_patient_status", table_name="admission_action_requests")
    op.drop_index("ix_admission_action_requests_created_by", table_name="admission_action_requests")
    op.drop_index("ix_admission_action_requests_status", table_name="admission_action_requests")
    op.drop_index("ix_admission_action_requests_request_type", table_name="admission_action_requests")
    op.drop_index("ix_admission_action_requests_rnica_assessment_id", table_name="admission_action_requests")
    op.drop_index("ix_admission_action_requests_patient_id", table_name="admission_action_requests")
    op.drop_index("ix_admission_action_requests_tenant_id", table_name="admission_action_requests")
    op.drop_table("admission_action_requests")
