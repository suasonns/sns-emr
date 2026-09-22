"""Extend clinical_outcome_records/idg_reviews for full outcome+follow-up
workflow and create idg_review_audit_events

Revision ID: c8a1f0d92b3e
Revises: 3fa1b52c68d4
Create Date: 2026-09-22

Adds the controlled outcome_status lifecycle (IDENTIFIED..
CLOSED_WITH_ONGOING_PLAN) and correction/reopen tracking to
clinical_outcome_records, adds the IDG follow-up detail fields
(desired_patient_outcome, follow_up_action, follow_up_due_date,
closure_summary, reopen tracking) to the existing idg_reviews table
(no new idg_follow_ups table), and creates a new per-domain
idg_review_audit_events table following the existing
patient_response_audit_events / compliance_audit_events pattern.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c8a1f0d92b3e"
down_revision = "3fa1b52c68d4"
branch_labels = None
depends_on = None

OUTCOME_STATUSES = (
    "IDENTIFIED",
    "ASSESSED",
    "INTERVENTION_IN_PROGRESS",
    "AWAITING_RESPONSE",
    "IDG_FOLLOW_UP_REQUIRED",
    "IDG_FOLLOW_UP_ASSIGNED",
    "IDG_FOLLOW_UP_COMPLETED",
    "IMPROVED",
    "RESOLVED",
    "PERSISTENT",
    "WORSENED",
    "TRANSFERRED_FOR_HIGHER_LEVEL_OF_CARE",
    "CLOSED_WITH_ONGOING_PLAN",
)


def upgrade() -> None:
    # -----------------------------------------------------------------
    # clinical_outcome_records
    # -----------------------------------------------------------------
    op.add_column(
        "clinical_outcome_records",
        sa.Column("outcome_status", sa.String(length=40), nullable=False, server_default="IDENTIFIED"),
    )
    op.add_column("clinical_outcome_records", sa.Column("closed_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("clinical_outcome_records", sa.Column("reopened_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("clinical_outcome_records", sa.Column("reopened_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("clinical_outcome_records", sa.Column("reopen_reason", sa.Text(), nullable=True))

    op.create_foreign_key(
        "fk_clinical_outcome_records_closed_by",
        "clinical_outcome_records",
        "users",
        ["closed_by"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_clinical_outcome_records_reopened_by",
        "clinical_outcome_records",
        "users",
        ["reopened_by"],
        ["id"],
    )

    op.create_index("ix_clinical_outcome_records_outcome_status", "clinical_outcome_records", ["outcome_status"])

    op.create_check_constraint(
        "ck_clinical_outcome_records_outcome_status",
        "clinical_outcome_records",
        "outcome_status IN (" + ",".join(f"'{s}'" for s in OUTCOME_STATUSES) + ")",
    )
    op.drop_constraint(
        "ck_clinical_outcome_records_persistent_requires_remaining_need", "clinical_outcome_records", type_="check"
    )
    op.create_check_constraint(
        "ck_clinical_outcome_records_persistent_requires_remaining_need",
        "clinical_outcome_records",
        "outcome_status NOT IN ('PERSISTENT','WORSENED','CLOSED_WITH_ONGOING_PLAN') OR remaining_need_identified = true",
    )
    op.create_check_constraint(
        "ck_clinical_outcome_records_reopen_requires_reason",
        "clinical_outcome_records",
        "reopened_at IS NULL OR reopen_reason IS NOT NULL",
    )

    # -----------------------------------------------------------------
    # idg_reviews follow-up detail extension
    # -----------------------------------------------------------------
    op.add_column("idg_reviews", sa.Column("desired_patient_outcome", sa.Text(), nullable=True))
    op.add_column("idg_reviews", sa.Column("follow_up_action", sa.Text(), nullable=True))
    op.add_column("idg_reviews", sa.Column("follow_up_due_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("idg_reviews", sa.Column("closure_summary", sa.Text(), nullable=True))
    op.add_column("idg_reviews", sa.Column("continuing_plan", sa.Text(), nullable=True))
    op.add_column("idg_reviews", sa.Column("reopened_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("idg_reviews", sa.Column("reopened_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("idg_reviews", sa.Column("reopen_reason", sa.Text(), nullable=True))

    op.create_check_constraint(
        "ck_idg_reviews_reopen_requires_reason",
        "idg_reviews",
        "reopened_at IS NULL OR reopen_reason IS NOT NULL",
    )
    op.create_check_constraint(
        "ck_idg_reviews_completion_requires_closure_summary",
        "idg_reviews",
        "follow_up_status != 'COMPLETED' OR closure_summary IS NOT NULL",
    )

    # -----------------------------------------------------------------
    # clinical_outcome_audit_events (new per-domain audit table)
    # -----------------------------------------------------------------
    op.create_table(
        "clinical_outcome_audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinical_outcome_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("admission_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_account_discipline", sa.String(length=50), nullable=True),
        sa.Column("prior_value", postgresql.JSONB(), nullable=True),
        sa.Column("new_value", postgresql.JSONB(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["clinical_outcome_record_id"], ["clinical_outcome_records.id"], name="fk_clinical_outcome_audit_events_record_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], name="fk_clinical_outcome_audit_events_patient_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name="fk_clinical_outcome_audit_events_actor_user_id"),
        sa.PrimaryKeyConstraint("id", name="pk_clinical_outcome_audit_events"),
        sa.CheckConstraint(
            "event_type IN ("
            "'OUTCOME_CREATED','INTERVENTION_RECORDED','PATIENT_RESPONSE_RECORDED',"
            "'OUTCOME_STATUS_CHANGED','REMAINING_NEED_RECORDED','IDG_FOLLOW_UP_REQUIRED',"
            "'OUTCOME_CORRECTED','OUTCOME_FINALIZED','OUTCOME_REOPENED'"
            ")",
            name="ck_clinical_outcome_audit_events_type",
        ),
    )
    op.create_index("ix_clinical_outcome_audit_events_tenant_id", "clinical_outcome_audit_events", ["tenant_id"])
    op.create_index("ix_clinical_outcome_audit_events_clinical_outcome_record_id", "clinical_outcome_audit_events", ["clinical_outcome_record_id"])
    op.create_index("ix_clinical_outcome_audit_events_patient_id", "clinical_outcome_audit_events", ["patient_id"])
    op.create_index("ix_clinical_outcome_audit_events_admission_id", "clinical_outcome_audit_events", ["admission_id"])
    op.create_index("ix_clinical_outcome_audit_events_event_type", "clinical_outcome_audit_events", ["event_type"])
    op.create_index("ix_clinical_outcome_audit_events_correlation_id", "clinical_outcome_audit_events", ["correlation_id"])
    op.create_index("ix_clinical_outcome_audit_events_created_at", "clinical_outcome_audit_events", ["created_at"])
    op.create_index(
        "ix_clinical_outcome_audit_events_tenant_event_created",
        "clinical_outcome_audit_events",
        ["tenant_id", "event_type", "created_at"],
    )

    # -----------------------------------------------------------------
    # idg_review_audit_events (new per-domain audit table)
    # -----------------------------------------------------------------
    op.create_table(
        "idg_review_audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("idg_review_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("admission_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_account_discipline", sa.String(length=50), nullable=True),
        sa.Column("prior_value", postgresql.JSONB(), nullable=True),
        sa.Column("new_value", postgresql.JSONB(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["idg_review_id"], ["idg_reviews.id"], name="fk_idg_review_audit_events_idg_review_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], name="fk_idg_review_audit_events_patient_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name="fk_idg_review_audit_events_actor_user_id"),
        sa.PrimaryKeyConstraint("id", name="pk_idg_review_audit_events"),
        sa.CheckConstraint(
            "event_type IN ("
            "'IDG_FOLLOW_UP_CREATED','IDG_RECOMMENDATION_RECORDED','FOLLOW_UP_ASSIGNED',"
            "'FOLLOW_UP_REASSIGNED','FOLLOW_UP_PROGRESS_RECORDED','PATIENT_RESPONSE_LINKED',"
            "'FOLLOW_UP_COMPLETED','FOLLOW_UP_REOPENED'"
            ")",
            name="ck_idg_review_audit_events_type",
        ),
    )
    op.create_index("ix_idg_review_audit_events_tenant_id", "idg_review_audit_events", ["tenant_id"])
    op.create_index("ix_idg_review_audit_events_idg_review_id", "idg_review_audit_events", ["idg_review_id"])
    op.create_index("ix_idg_review_audit_events_patient_id", "idg_review_audit_events", ["patient_id"])
    op.create_index("ix_idg_review_audit_events_admission_id", "idg_review_audit_events", ["admission_id"])
    op.create_index("ix_idg_review_audit_events_event_type", "idg_review_audit_events", ["event_type"])
    op.create_index("ix_idg_review_audit_events_correlation_id", "idg_review_audit_events", ["correlation_id"])
    op.create_index("ix_idg_review_audit_events_created_at", "idg_review_audit_events", ["created_at"])
    op.create_index(
        "ix_idg_review_audit_events_tenant_event_created",
        "idg_review_audit_events",
        ["tenant_id", "event_type", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_idg_review_audit_events_tenant_event_created", table_name="idg_review_audit_events")
    op.drop_index("ix_idg_review_audit_events_created_at", table_name="idg_review_audit_events")
    op.drop_index("ix_idg_review_audit_events_correlation_id", table_name="idg_review_audit_events")
    op.drop_index("ix_idg_review_audit_events_event_type", table_name="idg_review_audit_events")
    op.drop_index("ix_idg_review_audit_events_admission_id", table_name="idg_review_audit_events")
    op.drop_index("ix_idg_review_audit_events_patient_id", table_name="idg_review_audit_events")
    op.drop_index("ix_idg_review_audit_events_idg_review_id", table_name="idg_review_audit_events")
    op.drop_index("ix_idg_review_audit_events_tenant_id", table_name="idg_review_audit_events")
    op.drop_table("idg_review_audit_events")

    op.drop_index("ix_clinical_outcome_audit_events_tenant_event_created", table_name="clinical_outcome_audit_events")
    op.drop_index("ix_clinical_outcome_audit_events_created_at", table_name="clinical_outcome_audit_events")
    op.drop_index("ix_clinical_outcome_audit_events_correlation_id", table_name="clinical_outcome_audit_events")
    op.drop_index("ix_clinical_outcome_audit_events_event_type", table_name="clinical_outcome_audit_events")
    op.drop_index("ix_clinical_outcome_audit_events_admission_id", table_name="clinical_outcome_audit_events")
    op.drop_index("ix_clinical_outcome_audit_events_patient_id", table_name="clinical_outcome_audit_events")
    op.drop_index("ix_clinical_outcome_audit_events_clinical_outcome_record_id", table_name="clinical_outcome_audit_events")
    op.drop_index("ix_clinical_outcome_audit_events_tenant_id", table_name="clinical_outcome_audit_events")
    op.drop_table("clinical_outcome_audit_events")

    op.drop_constraint("ck_idg_reviews_completion_requires_closure_summary", "idg_reviews", type_="check")
    op.drop_constraint("ck_idg_reviews_reopen_requires_reason", "idg_reviews", type_="check")
    op.drop_column("idg_reviews", "reopen_reason")
    op.drop_column("idg_reviews", "reopened_by")
    op.drop_column("idg_reviews", "reopened_at")
    op.drop_column("idg_reviews", "continuing_plan")
    op.drop_column("idg_reviews", "closure_summary")
    op.drop_column("idg_reviews", "follow_up_due_date")
    op.drop_column("idg_reviews", "follow_up_action")
    op.drop_column("idg_reviews", "desired_patient_outcome")

    op.drop_constraint("ck_clinical_outcome_records_reopen_requires_reason", "clinical_outcome_records", type_="check")
    op.drop_constraint(
        "ck_clinical_outcome_records_persistent_requires_remaining_need", "clinical_outcome_records", type_="check"
    )
    op.create_check_constraint(
        "ck_clinical_outcome_records_persistent_requires_remaining_need",
        "clinical_outcome_records",
        "patient_response_status NOT IN ('PERSISTENT','WORSENED') OR remaining_need_identified = true",
    )
    op.drop_constraint("ck_clinical_outcome_records_outcome_status", "clinical_outcome_records", type_="check")
    op.drop_index("ix_clinical_outcome_records_outcome_status", table_name="clinical_outcome_records")
    op.drop_constraint("fk_clinical_outcome_records_reopened_by", "clinical_outcome_records", type_="foreignkey")
    op.drop_constraint("fk_clinical_outcome_records_closed_by", "clinical_outcome_records", type_="foreignkey")
    op.drop_column("clinical_outcome_records", "reopen_reason")
    op.drop_column("clinical_outcome_records", "reopened_by")
    op.drop_column("clinical_outcome_records", "reopened_at")
    op.drop_column("clinical_outcome_records", "closed_by")
    op.drop_column("clinical_outcome_records", "outcome_status")
