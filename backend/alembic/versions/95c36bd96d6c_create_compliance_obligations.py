"""Create compliance_obligations and compliance_audit_events

Revision ID: 95c36bd96d6c
Revises: 23062ecb4fd9
Create Date: 2026-09-21

Generic regulatory-obligation tracking for the shared SNS compliance
framework (issue #145), used only where no more specific domain record
already exists (election addendum, HOPE submission, two-hour response,
IDG follow-up each have their own dedicated tracking).
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "95c36bd96d6c"
down_revision = "23062ecb4fd9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "compliance_obligations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("admission_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("benefit_period_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("obligation_type", sa.String(length=64), nullable=False),
        sa.Column("regulatory_basis", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="OPEN"),
        sa.Column("required_by_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completion_evidence_reference", sa.String(length=255), nullable=True),
        sa.Column("assigned_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_record_type", sa.String(length=64), nullable=True),
        sa.Column("source_record_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_compliance_obligations_tenant_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], name="fk_compliance_obligations_patient_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["admission_id"], ["admissions.id"], name="fk_compliance_obligations_admission_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["benefit_period_id"], ["benefit_periods.id"], name="fk_compliance_obligations_benefit_period_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_user_id"], ["users.id"], name="fk_compliance_obligations_assigned_user_id"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_compliance_obligations_created_by"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], name="fk_compliance_obligations_updated_by"),
        sa.PrimaryKeyConstraint("id", name="pk_compliance_obligations"),
        sa.CheckConstraint(
            "status IN ('OPEN','IN_PROGRESS','COMPLETED','OVERDUE','WAIVED','VOIDED')",
            name="ck_compliance_obligations_status",
        ),
        sa.CheckConstraint(
            "status != 'COMPLETED' OR completed_at IS NOT NULL",
            name="ck_compliance_obligations_completed_requires_timestamp",
        ),
    )
    op.create_index("ix_compliance_obligations_tenant_id", "compliance_obligations", ["tenant_id"])
    op.create_index("ix_compliance_obligations_patient_id", "compliance_obligations", ["patient_id"])
    op.create_index("ix_compliance_obligations_admission_id", "compliance_obligations", ["admission_id"])
    op.create_index("ix_compliance_obligations_benefit_period_id", "compliance_obligations", ["benefit_period_id"])
    op.create_index("ix_compliance_obligations_obligation_type", "compliance_obligations", ["obligation_type"])
    op.create_index(
        "ix_compliance_obligations_tenant_status_due",
        "compliance_obligations",
        ["tenant_id", "status", "required_by_at"],
    )
    op.create_index(
        "ix_compliance_obligations_tenant_patient", "compliance_obligations", ["tenant_id", "patient_id"]
    )

    op.create_table(
        "compliance_audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("compliance_obligation_id", postgresql.UUID(as_uuid=True), nullable=False),
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
            ["compliance_obligation_id"],
            ["compliance_obligations.id"],
            name="fk_compliance_audit_events_compliance_obligation_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], name="fk_compliance_audit_events_patient_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name="fk_compliance_audit_events_actor_user_id"),
        sa.PrimaryKeyConstraint("id", name="pk_compliance_audit_events"),
        sa.CheckConstraint(
            "event_type IN ("
            "'REQUIREMENT_CREATED','DEADLINE_CALCULATED','ASSIGNED','DEADLINE_MISSED',"
            "'RECORD_CORRECTED','RECORD_FINALIZED','RECORD_REOPENED'"
            ")",
            name="ck_compliance_audit_events_type",
        ),
    )
    op.create_index("ix_compliance_audit_events_tenant_id", "compliance_audit_events", ["tenant_id"])
    op.create_index(
        "ix_compliance_audit_events_compliance_obligation_id",
        "compliance_audit_events",
        ["compliance_obligation_id"],
    )
    op.create_index("ix_compliance_audit_events_patient_id", "compliance_audit_events", ["patient_id"])
    op.create_index("ix_compliance_audit_events_admission_id", "compliance_audit_events", ["admission_id"])
    op.create_index("ix_compliance_audit_events_event_type", "compliance_audit_events", ["event_type"])
    op.create_index("ix_compliance_audit_events_correlation_id", "compliance_audit_events", ["correlation_id"])
    op.create_index("ix_compliance_audit_events_created_at", "compliance_audit_events", ["created_at"])
    op.create_index(
        "ix_compliance_audit_events_tenant_event_created",
        "compliance_audit_events",
        ["tenant_id", "event_type", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("compliance_audit_events")
    op.drop_table("compliance_obligations")
