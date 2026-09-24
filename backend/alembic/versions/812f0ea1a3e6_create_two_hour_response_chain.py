"""Create California two-hour patient response chain

Revision ID: 812f0ea1a3e6
Revises: 95c36bd96d6c
Create Date: 2026-09-21

California Title 22 Section 74820/74848 two-hour in-person licensed-nurse
response requirement (issue #143). Clock: START =
patient_response_events.received_at, STOP =
nurse_response_assignments.arrived_at (in-person arrival only).
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "812f0ea1a3e6"
down_revision = "95c36bd96d6c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patient_response_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("admission_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("benefit_period_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_via", sa.String(length=40), nullable=True),
        sa.Column("reported_by_name", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("response_deadline_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closure_requires_patient_response", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_patient_response_events_tenant_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], name="fk_patient_response_events_patient_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["admission_id"], ["admissions.id"], name="fk_patient_response_events_admission_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["benefit_period_id"], ["benefit_periods.id"], name="fk_patient_response_events_benefit_period_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_patient_response_events_created_by"),
        sa.PrimaryKeyConstraint("id", name="pk_patient_response_events"),
        sa.CheckConstraint(
            "event_type IN ('MEDICAL_NEED','SAFETY_CONCERN')", name="ck_patient_response_events_event_type"
        ),
    )
    op.create_index("ix_patient_response_events_tenant_id", "patient_response_events", ["tenant_id"])
    op.create_index("ix_patient_response_events_patient_id", "patient_response_events", ["patient_id"])
    op.create_index("ix_patient_response_events_admission_id", "patient_response_events", ["admission_id"])
    op.create_index(
        "ix_patient_response_events_benefit_period_id", "patient_response_events", ["benefit_period_id"]
    )
    op.create_index(
        "ix_patient_response_events_tenant_deadline",
        "patient_response_events",
        ["tenant_id", "response_deadline_at"],
    )
    op.create_index(
        "ix_patient_response_events_tenant_patient", "patient_response_events", ["tenant_id", "patient_id"]
    )

    op.create_table(
        "nurse_response_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_response_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nurse_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("arrived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reassigned_from_assignment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reassignment_reason", sa.Text(), nullable=True),
        sa.Column("is_late", sa.Boolean(), nullable=True),
        sa.Column("variance_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["patient_response_event_id"],
            ["patient_response_events.id"],
            name="fk_nurse_response_assignments_patient_response_event_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["nurse_user_id"], ["users.id"], name="fk_nurse_response_assignments_nurse_user_id"),
        sa.ForeignKeyConstraint(
            ["reassigned_from_assignment_id"],
            ["nurse_response_assignments.id"],
            name="fk_nurse_response_assignments_reassigned_from",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_nurse_response_assignments_created_by"),
        sa.PrimaryKeyConstraint("id", name="pk_nurse_response_assignments"),
        sa.CheckConstraint(
            "reassigned_from_assignment_id IS NULL OR reassigned_from_assignment_id != id",
            name="ck_nurse_response_assignments_no_self_reassign",
        ),
        sa.CheckConstraint(
            "is_late IS NULL OR is_late = false OR variance_reason IS NOT NULL",
            name="ck_nurse_response_assignments_late_requires_variance_reason",
        ),
    )
    op.create_index("ix_nurse_response_assignments_tenant_id", "nurse_response_assignments", ["tenant_id"])
    op.create_index(
        "ix_nurse_response_assignments_patient_response_event_id",
        "nurse_response_assignments",
        ["patient_response_event_id"],
    )

    op.create_table(
        "interim_patient_support",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_response_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("support_type", sa.String(length=40), nullable=False),
        sa.Column("provided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provided_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["patient_response_event_id"],
            ["patient_response_events.id"],
            name="fk_interim_patient_support_patient_response_event_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["provided_by_user_id"], ["users.id"], name="fk_interim_patient_support_provided_by_user_id"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_interim_patient_support_created_by"),
        sa.PrimaryKeyConstraint("id", name="pk_interim_patient_support"),
    )
    op.create_index("ix_interim_patient_support_tenant_id", "interim_patient_support", ["tenant_id"])
    op.create_index(
        "ix_interim_patient_support_patient_response_event_id",
        "interim_patient_support",
        ["patient_response_event_id"],
    )

    op.create_table(
        "response_interventions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_response_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nurse_response_assignment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("intervention_type", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("performed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("patient_response_recorded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("patient_response_summary", sa.Text(), nullable=True),
        sa.Column("idg_notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["patient_response_event_id"],
            ["patient_response_events.id"],
            name="fk_response_interventions_patient_response_event_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["nurse_response_assignment_id"],
            ["nurse_response_assignments.id"],
            name="fk_response_interventions_nurse_response_assignment_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["performed_by_user_id"], ["users.id"], name="fk_response_interventions_performed_by_user_id"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_response_interventions_created_by"),
        sa.PrimaryKeyConstraint("id", name="pk_response_interventions"),
    )
    op.create_index("ix_response_interventions_tenant_id", "response_interventions", ["tenant_id"])
    op.create_index(
        "ix_response_interventions_patient_response_event_id",
        "response_interventions",
        ["patient_response_event_id"],
    )

    op.create_table(
        "patient_response_audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_response_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("admission_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_account_discipline", sa.String(length=50), nullable=True),
        sa.Column("prior_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["patient_response_event_id"],
            ["patient_response_events.id"],
            name="fk_patient_response_audit_events_patient_response_event_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], name="fk_patient_response_audit_events_patient_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name="fk_patient_response_audit_events_actor_user_id"),
        sa.PrimaryKeyConstraint("id", name="pk_patient_response_audit_events"),
        sa.CheckConstraint(
            "event_type IN ("
            "'REQUIREMENT_CREATED','ASSIGNED','REASSIGNED','DISPATCHED','ARRIVED',"
            "'INTERIM_SUPPORT_RECORDED','ASSESSMENT_RECORDED','INTERVENTION_RECORDED',"
            "'PATIENT_RESPONSE_RECORDED','IDG_NOTIFIED','DEADLINE_MISSED',"
            "'RECORD_CORRECTED','RECORD_FINALIZED'"
            ")",
            name="ck_patient_response_audit_events_type",
        ),
    )
    op.create_index("ix_patient_response_audit_events_tenant_id", "patient_response_audit_events", ["tenant_id"])
    op.create_index(
        "ix_patient_response_audit_events_patient_response_event_id",
        "patient_response_audit_events",
        ["patient_response_event_id"],
    )
    op.create_index("ix_patient_response_audit_events_patient_id", "patient_response_audit_events", ["patient_id"])
    op.create_index("ix_patient_response_audit_events_admission_id", "patient_response_audit_events", ["admission_id"])
    op.create_index("ix_patient_response_audit_events_event_type", "patient_response_audit_events", ["event_type"])
    op.create_index("ix_patient_response_audit_events_correlation_id", "patient_response_audit_events", ["correlation_id"])
    op.create_index("ix_patient_response_audit_events_created_at", "patient_response_audit_events", ["created_at"])
    op.create_index(
        "ix_patient_response_audit_events_tenant_event_created",
        "patient_response_audit_events",
        ["tenant_id", "event_type", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("patient_response_audit_events")
    op.drop_table("response_interventions")
    op.drop_table("interim_patient_support")
    op.drop_table("nurse_response_assignments")
    op.drop_table("patient_response_events")
