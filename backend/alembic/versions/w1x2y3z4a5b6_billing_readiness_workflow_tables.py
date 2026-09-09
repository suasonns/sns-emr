"""Sprint 2 -- Billing Readiness Operational Workflow: blocker records,
generic assignment/follow-up tracking, and shared workflow audit trail.

Adds four additive tables on top of the Sprint 1 (Eligibility
Traceability Epic) persistence foundation:

  - billing_blocker_records: typed, per-blocker lifecycle overlay on top
    of BillingReadinessVerdict.blockers (free text is unchanged/untouched).
  - readiness_assignments: generic "who owns this right now" assignment,
    not a biller/agency-specific concept.
  - readiness_follow_ups: generic due-date/resolution workflow tracking.
  - readiness_workflow_events: single shared audit trail for every state
    change across the three tables above, mirroring the existing
    BenefitPeriodStatusEvent append-only pattern (a sibling table, not a
    competing audit mechanism).

Purely additive -- no existing table, column, or migration in the chain
is altered.

Revision ID: w1x2y3z4a5b6
Revises: v3w4x5y6z7a8
Create Date: 2026-09-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "w1x2y3z4a5b6"
down_revision: Union[str, Sequence[str], None] = "v3w4x5y6z7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------
    # billing_blocker_records
    # ---------------------------------------------------------
    op.create_table(
        "billing_blocker_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("blocker_code", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("first_seen_verdict_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("billing_readiness_verdicts.id"), nullable=False),
        sa.Column("last_seen_verdict_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("billing_readiness_verdicts.id"), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("status", sa.String(length=16), server_default="OPEN", nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(length=64), nullable=True),
        sa.Column("resolution_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_billing_blocker_records")),
    )
    op.create_index("ix_billing_blocker_records_tenant_id", "billing_blocker_records", ["tenant_id"])
    op.create_index("ix_billing_blocker_records_patient_id", "billing_blocker_records", ["patient_id"])
    op.create_index("ix_billing_blocker_records_blocker_code", "billing_blocker_records", ["blocker_code"])
    op.create_index("ix_billing_blocker_records_status", "billing_blocker_records", ["status"])
    op.create_index("ix_bbr_patient_status", "billing_blocker_records", ["patient_id", "status"])
    op.create_index("ix_bbr_tenant_status", "billing_blocker_records", ["tenant_id", "status"])

    # ---------------------------------------------------------
    # readiness_assignments
    # ---------------------------------------------------------
    op.create_table(
        "readiness_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("assigned_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("assigned_role", sa.String(length=64), nullable=True),
        sa.Column("assigned_date", sa.Date(), nullable=True),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("assignment_status", sa.String(length=16), server_default="UNASSIGNED", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_readiness_assignments")),
    )
    op.create_index("ix_readiness_assignments_tenant_id", "readiness_assignments", ["tenant_id"])
    op.create_index("ix_readiness_assignments_patient_id", "readiness_assignments", ["patient_id"])
    op.create_index("ix_readiness_assignments_assigned_user_id", "readiness_assignments", ["assigned_user_id"])
    op.create_index("ix_readiness_assignments_assigned_by", "readiness_assignments", ["assigned_by"])
    op.create_index("ix_readiness_assignments_assignment_status", "readiness_assignments", ["assignment_status"])
    op.create_index("ix_readiness_assignments_tenant_patient", "readiness_assignments", ["tenant_id", "patient_id"])
    op.create_index("ix_readiness_assignments_status", "readiness_assignments", ["assignment_status"])

    # ---------------------------------------------------------
    # readiness_follow_ups
    # ---------------------------------------------------------
    op.create_table(
        "readiness_follow_ups",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("readiness_assignments.id"), nullable=True),
        sa.Column("follow_up_required", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("status", sa.String(length=16), server_default="OPEN", nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("resolved_date", sa.Date(), nullable=True),
        sa.Column("created_date", sa.Date(), server_default=sa.text("current_date"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_readiness_follow_ups")),
    )
    op.create_index("ix_readiness_follow_ups_tenant_id", "readiness_follow_ups", ["tenant_id"])
    op.create_index("ix_readiness_follow_ups_patient_id", "readiness_follow_ups", ["patient_id"])
    op.create_index("ix_readiness_follow_ups_assignment_id", "readiness_follow_ups", ["assignment_id"])
    op.create_index("ix_readiness_follow_ups_status", "readiness_follow_ups", ["status"])
    op.create_index("ix_readiness_follow_ups_tenant_status", "readiness_follow_ups", ["tenant_id", "status"])
    op.create_index("ix_readiness_follow_ups_patient_status", "readiness_follow_ups", ["patient_id", "status"])
    op.create_index("ix_readiness_follow_ups_due_date", "readiness_follow_ups", ["due_date"])

    # ---------------------------------------------------------
    # readiness_workflow_events
    # ---------------------------------------------------------
    op.create_table(
        "readiness_workflow_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(length=16), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("previous_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("related_verdict_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("billing_readiness_verdicts.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_readiness_workflow_events")),
    )
    op.create_index("ix_readiness_workflow_events_tenant_id", "readiness_workflow_events", ["tenant_id"])
    op.create_index("ix_readiness_workflow_events_entity_type", "readiness_workflow_events", ["entity_type"])
    op.create_index("ix_readiness_workflow_events_entity_id", "readiness_workflow_events", ["entity_id"])
    op.create_index("ix_readiness_workflow_events_event_type", "readiness_workflow_events", ["event_type"])
    op.create_index("ix_readiness_workflow_events_actor_user_id", "readiness_workflow_events", ["actor_user_id"])
    op.create_index("ix_readiness_workflow_events_occurred_at", "readiness_workflow_events", ["occurred_at"])
    op.create_index("ix_readiness_workflow_events_related_verdict_id", "readiness_workflow_events", ["related_verdict_id"])
    op.create_index("ix_rwe_entity", "readiness_workflow_events", ["entity_type", "entity_id", "occurred_at"])
    op.create_index("ix_rwe_tenant_occurred", "readiness_workflow_events", ["tenant_id", "occurred_at"])


def downgrade() -> None:
    op.drop_table("readiness_workflow_events")
    op.drop_table("readiness_follow_ups")
    op.drop_table("readiness_assignments")
    op.drop_table("billing_blocker_records")
