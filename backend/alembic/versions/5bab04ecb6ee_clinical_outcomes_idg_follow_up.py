"""Create clinical_outcome_records and extend idg_reviews for follow-up

Revision ID: 5bab04ecb6ee
Revises: 812f0ea1a3e6
Create Date: 2026-09-21

Clinical-outcome tracking for the two-hour response requirement. IDG
follow-up is tracked by extending the existing idg_reviews table rather
than creating a second, parallel idg_follow_ups table (idg_reviews
already carries patient/benefit_period/finalization state for exactly
this purpose).
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "5bab04ecb6ee"
down_revision = "812f0ea1a3e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinical_outcome_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("admission_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("benefit_period_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("patient_response_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_visit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("patient_appropriately_cared_for", sa.Boolean(), nullable=True),
        sa.Column("patient_response_status", sa.String(length=30), nullable=True),
        sa.Column("remaining_need_identified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("idg_communicated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("idg_communicated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("intervention_timely", sa.Boolean(), nullable=True),
        sa.Column("documentation_complete", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("idg_review_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("response_recorded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by_account_discipline", sa.String(length=50), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_clinical_outcome_records_tenant_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], name="fk_clinical_outcome_records_patient_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["admission_id"], ["admissions.id"], name="fk_clinical_outcome_records_admission_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["benefit_period_id"], ["benefit_periods.id"], name="fk_clinical_outcome_records_benefit_period_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["patient_response_event_id"], ["patient_response_events.id"], name="fk_clinical_outcome_records_patient_response_event_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_task_id"], ["tasks.id"], name="fk_clinical_outcome_records_source_task_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_visit_id"], ["visits.id"], name="fk_clinical_outcome_records_source_visit_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["idg_review_id"], ["idg_reviews.id"], name="fk_clinical_outcome_records_idg_review_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_clinical_outcome_records_created_by"),
        sa.PrimaryKeyConstraint("id", name="pk_clinical_outcome_records"),
        sa.CheckConstraint(
            "closed_at IS NULL OR response_recorded_at IS NOT NULL",
            name="ck_clinical_outcome_records_closure_requires_response",
        ),
        sa.CheckConstraint(
            "patient_response_status NOT IN ('PERSISTENT','WORSENED') OR remaining_need_identified = true",
            name="ck_clinical_outcome_records_persistent_requires_remaining_need",
        ),
    )
    op.create_index("ix_clinical_outcome_records_tenant_id", "clinical_outcome_records", ["tenant_id"])
    op.create_index("ix_clinical_outcome_records_patient_id", "clinical_outcome_records", ["patient_id"])
    op.create_index("ix_clinical_outcome_records_admission_id", "clinical_outcome_records", ["admission_id"])
    op.create_index("ix_clinical_outcome_records_benefit_period_id", "clinical_outcome_records", ["benefit_period_id"])
    op.create_index("ix_clinical_outcome_records_patient_response_event_id", "clinical_outcome_records", ["patient_response_event_id"])
    op.create_index("ix_clinical_outcome_records_idg_review_id", "clinical_outcome_records", ["idg_review_id"])
    op.create_index(
        "ix_clinical_outcome_records_tenant_patient", "clinical_outcome_records", ["tenant_id", "patient_id"]
    )

    # ---------------------------------------------------------
    # Extend idg_reviews for follow-up tracking (instead of creating a
    # second idg_follow_ups table)
    # ---------------------------------------------------------
    op.add_column("idg_reviews", sa.Column("follow_up_required", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("idg_reviews", sa.Column("follow_up_status", sa.String(length=20), nullable=True))
    op.add_column("idg_reviews", sa.Column("follow_up_assigned_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("idg_reviews", sa.Column("follow_up_assigned_to_user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("idg_reviews", sa.Column("follow_up_completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("idg_reviews", sa.Column("source_patient_response_event_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("idg_reviews", sa.Column("source_clinical_outcome_record_id", postgresql.UUID(as_uuid=True), nullable=True))

    op.create_index(
        "ix_idg_reviews_tenant_follow_up_status", "idg_reviews", ["tenant_id", "follow_up_status"]
    )
    op.create_index(
        "ix_idg_reviews_source_patient_response_event_id", "idg_reviews", ["source_patient_response_event_id"]
    )
    op.create_index(
        "ix_idg_reviews_source_clinical_outcome_record_id",
        "idg_reviews",
        ["source_clinical_outcome_record_id"],
    )
    op.create_check_constraint(
        "ck_idg_reviews_follow_up_completion_requires_timestamp",
        "idg_reviews",
        "follow_up_status != 'COMPLETED' OR follow_up_completed_at IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_constraint("ck_idg_reviews_follow_up_completion_requires_timestamp", "idg_reviews", type_="check")
    op.drop_index("ix_idg_reviews_source_clinical_outcome_record_id", table_name="idg_reviews")
    op.drop_index("ix_idg_reviews_source_patient_response_event_id", table_name="idg_reviews")
    op.drop_index("ix_idg_reviews_tenant_follow_up_status", table_name="idg_reviews")
    op.drop_column("idg_reviews", "source_clinical_outcome_record_id")
    op.drop_column("idg_reviews", "source_patient_response_event_id")
    op.drop_column("idg_reviews", "follow_up_completed_at")
    op.drop_column("idg_reviews", "follow_up_assigned_to_user_id")
    op.drop_column("idg_reviews", "follow_up_assigned_at")
    op.drop_column("idg_reviews", "follow_up_status")
    op.drop_column("idg_reviews", "follow_up_required")

    op.drop_table("clinical_outcome_records")
