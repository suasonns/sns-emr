"""Extend rnica_assessments for HOPE submission tracking

Revision ID: aa9e08e3848e
Revises: 5bab04ecb6ee
Create Date: 2026-09-21

RnicaAssessment remains the single authoritative HOPE workflow/submission
record. This adds submission-tracking fields to it and a child table for
individual submission attempts -- it does NOT create a second
hope_records/hope_submission_obligation table, and does NOT add a second
status column (hope_workflow_status remains the single status owner).
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "aa9e08e3848e"
down_revision = "5bab04ecb6ee"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rnica_assessments", sa.Column("hope_event_type", sa.String(length=20), nullable=True))
    op.add_column("rnica_assessments", sa.Column("hope_event_date", sa.Date(), nullable=True))
    op.add_column(
        "rnica_assessments", sa.Column("hope_submission_due_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("rnica_assessments", sa.Column("hope_overdue_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("rnica_assessments", sa.Column("hope_receipt_reference", sa.String(length=128), nullable=True))
    op.add_column("rnica_assessments", sa.Column("hope_validation_status", sa.String(length=32), nullable=True))
    op.add_column("rnica_assessments", sa.Column("hope_accepted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("rnica_assessments", sa.Column("hope_rejected_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "rnica_assessments",
        sa.Column("hope_correction_required", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "rnica_assessments",
        sa.Column("hope_corrected_assessment_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "rnica_assessments", sa.Column("hope_last_submission_attempt_at", sa.DateTime(timezone=True), nullable=True)
    )

    op.create_foreign_key(
        "fk_rnica_assessments_hope_corrected_assessment_id",
        "rnica_assessments",
        "rnica_assessments",
        ["hope_corrected_assessment_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_index(
        "ix_rnica_assessments_tenant_status_due",
        "rnica_assessments",
        ["tenant_id", "hope_workflow_status", "hope_submission_due_at"],
    )
    op.create_index(
        "ix_rnica_assessments_tenant_admission_event",
        "rnica_assessments",
        ["tenant_id", "admission_id", "hope_event_type"],
    )
    op.create_index(
        "ix_rnica_assessments_tenant_overdue", "rnica_assessments", ["tenant_id", "hope_overdue_at"]
    )

    op.create_check_constraint(
        "ck_rnica_assessments_due_requires_event_date",
        "rnica_assessments",
        "hope_submission_due_at IS NULL OR hope_event_date IS NOT NULL",
    )
    op.create_check_constraint(
        "ck_rnica_assessments_accept_reject_mutually_exclusive",
        "rnica_assessments",
        "hope_accepted_at IS NULL OR hope_rejected_at IS NULL",
    )
    op.create_check_constraint(
        "ck_rnica_assessments_no_self_correction",
        "rnica_assessments",
        "hope_corrected_assessment_id IS NULL OR hope_corrected_assessment_id != id",
    )
    op.create_check_constraint(
        "ck_rnica_assessments_correction_required_flag",
        "rnica_assessments",
        "hope_workflow_status != 'CORRECTION_REQUIRED' OR hope_correction_required = true",
    )

    op.create_table(
        "rnica_hope_submission_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rnica_assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submission_number", sa.String(length=128), nullable=True),
        sa.Column("receipt_reference", sa.String(length=128), nullable=True),
        sa.Column("validation_status", sa.String(length=32), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("warning_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("correction_reason", sa.Text(), nullable=True),
        sa.Column("supersedes_attempt_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["rnica_assessment_id"],
            ["rnica_assessments.id"],
            name="fk_rnica_hope_submission_attempts_rnica_assessment_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_attempt_id"],
            ["rnica_hope_submission_attempts.id"],
            name="fk_rnica_hope_submission_attempts_supersedes_attempt_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_rnica_hope_submission_attempts_created_by"),
        sa.PrimaryKeyConstraint("id", name="pk_rnica_hope_submission_attempts"),
        sa.UniqueConstraint(
            "rnica_assessment_id", "attempt_number", name="uq_rnica_hope_submission_attempts_assessment_attempt"
        ),
        sa.CheckConstraint("attempt_number > 0", name="ck_rnica_hope_submission_attempts_attempt_positive"),
        sa.CheckConstraint(
            "accepted_at IS NULL OR rejected_at IS NULL",
            name="ck_rnica_hope_submission_attempts_accept_reject_mutually_exclusive",
        ),
        sa.CheckConstraint(
            "supersedes_attempt_id IS NULL OR supersedes_attempt_id != id",
            name="ck_rnica_hope_submission_attempts_no_self_supersede",
        ),
    )
    op.create_index(
        "ix_rnica_hope_submission_attempts_tenant_id", "rnica_hope_submission_attempts", ["tenant_id"]
    )
    op.create_index(
        "ix_rnica_hope_submission_attempts_rnica_assessment_id",
        "rnica_hope_submission_attempts",
        ["rnica_assessment_id"],
    )


def downgrade() -> None:
    op.drop_table("rnica_hope_submission_attempts")

    op.drop_constraint("ck_rnica_assessments_correction_required_flag", "rnica_assessments", type_="check")
    op.drop_constraint("ck_rnica_assessments_no_self_correction", "rnica_assessments", type_="check")
    op.drop_constraint("ck_rnica_assessments_accept_reject_mutually_exclusive", "rnica_assessments", type_="check")
    op.drop_constraint("ck_rnica_assessments_due_requires_event_date", "rnica_assessments", type_="check")

    op.drop_index("ix_rnica_assessments_tenant_overdue", table_name="rnica_assessments")
    op.drop_index("ix_rnica_assessments_tenant_admission_event", table_name="rnica_assessments")
    op.drop_index("ix_rnica_assessments_tenant_status_due", table_name="rnica_assessments")

    op.drop_constraint(
        "fk_rnica_assessments_hope_corrected_assessment_id", "rnica_assessments", type_="foreignkey"
    )

    op.drop_column("rnica_assessments", "hope_last_submission_attempt_at")
    op.drop_column("rnica_assessments", "hope_corrected_assessment_id")
    op.drop_column("rnica_assessments", "hope_correction_required")
    op.drop_column("rnica_assessments", "hope_rejected_at")
    op.drop_column("rnica_assessments", "hope_accepted_at")
    op.drop_column("rnica_assessments", "hope_validation_status")
    op.drop_column("rnica_assessments", "hope_receipt_reference")
    op.drop_column("rnica_assessments", "hope_overdue_at")
    op.drop_column("rnica_assessments", "hope_submission_due_at")
    op.drop_column("rnica_assessments", "hope_event_date")
    op.drop_column("rnica_assessments", "hope_event_type")
