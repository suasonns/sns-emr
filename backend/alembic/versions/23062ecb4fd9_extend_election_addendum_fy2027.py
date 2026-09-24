"""Extend election_addendum_requests for CMS FY2027 mandatory addendum rule

Revision ID: 23062ecb4fd9
Revises: um2d1c2c3o5u9
Create Date: 2026-09-21

Extends the existing election_addendum_requests table (the single
addendum authority) to also support the CMS-1851-F / FY2027 mandatory-
for-every-Medicare-election workflow, alongside the pre-existing
request-triggered workflow. Adds a determinations child table and a
domain audit-events table. Does NOT create a second, parallel
hospice_election_addendum parent table.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "23062ecb4fd9"
down_revision = "um2d1c2c3o5u9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---------------------------------------------------------
    # Extend election_addendum_requests
    # ---------------------------------------------------------
    op.alter_column(
        "election_addendum_requests", "requested_date", existing_type=sa.Date(), nullable=True
    )
    op.alter_column(
        "election_addendum_requests",
        "requested_by",
        existing_type=sa.String(length=32),
        nullable=True,
    )

    op.add_column(
        "election_addendum_requests",
        sa.Column("admission_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "election_addendum_requests",
        sa.Column(
            "trigger_type",
            sa.String(length=40),
            nullable=False,
            server_default="BENEFICIARY_REQUEST",
        ),
    )
    op.add_column(
        "election_addendum_requests", sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "election_addendum_requests", sa.Column("election_effective_date", sa.Date(), nullable=True)
    )
    op.add_column(
        "election_addendum_requests", sa.Column("required_by_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "election_addendum_requests",
        sa.Column("mandatory_rule_applies", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "election_addendum_requests",
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "election_addendum_requests",
        sa.Column("supersedes_request_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "election_addendum_requests",
        sa.Column("determination_completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "election_addendum_requests",
        sa.Column("determined_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "election_addendum_requests",
        sa.Column("determined_by_account_discipline", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "election_addendum_requests", sa.Column("furnished_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "election_addendum_requests",
        sa.Column("furnished_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "election_addendum_requests", sa.Column("furnished_to_type", sa.String(length=20), nullable=True)
    )
    op.add_column(
        "election_addendum_requests", sa.Column("furnished_to_name", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "election_addendum_requests", sa.Column("delivery_method", sa.String(length=40), nullable=True)
    )
    op.add_column(
        "election_addendum_requests",
        sa.Column("acknowledgment_status", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "election_addendum_requests", sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("election_addendum_requests", sa.Column("refusal_reason", sa.Text(), nullable=True))
    op.add_column(
        "election_addendum_requests",
        sa.Column("bfcc_qio_information_furnished", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "election_addendum_requests", sa.Column("document_reference", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "election_addendum_requests", sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "election_addendum_requests",
        sa.Column("finalized_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.create_foreign_key(
        "fk_election_addendum_requests_admission_id_admissions",
        "election_addendum_requests",
        "admissions",
        ["admission_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_election_addendum_requests_supersedes_request_id",
        "election_addendum_requests",
        "election_addendum_requests",
        ["supersedes_request_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_election_addendum_requests_determined_by_user_id",
        "election_addendum_requests",
        "users",
        ["determined_by_user_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_election_addendum_requests_furnished_by_user_id",
        "election_addendum_requests",
        "users",
        ["furnished_by_user_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_election_addendum_requests_finalized_by_user_id",
        "election_addendum_requests",
        "users",
        ["finalized_by_user_id"],
        ["id"],
    )

    op.create_index(
        "ix_election_addendum_requests_tenant_admission",
        "election_addendum_requests",
        ["tenant_id", "admission_id"],
    )
    op.create_index("ix_election_addendum_requests_admission_id", "election_addendum_requests", ["admission_id"])
    op.create_unique_constraint(
        "uq_election_addendum_requests_tenant_admission_version",
        "election_addendum_requests",
        ["tenant_id", "admission_id", "version_number"],
    )
    op.create_check_constraint(
        "ck_election_addendum_requests_version_positive",
        "election_addendum_requests",
        "version_number > 0",
    )
    op.create_check_constraint(
        "ck_election_addendum_requests_no_self_supersede",
        "election_addendum_requests",
        "supersedes_request_id IS NULL OR supersedes_request_id != id",
    )
    op.create_check_constraint(
        "ck_election_addendum_requests_ack_requires_timestamp",
        "election_addendum_requests",
        "acknowledgment_status != 'ACKNOWLEDGED' OR acknowledged_at IS NOT NULL",
    )
    op.create_check_constraint(
        "ck_election_addendum_requests_refusal_requires_reason",
        "election_addendum_requests",
        "acknowledgment_status != 'REFUSED' OR refusal_reason IS NOT NULL",
    )
    op.create_check_constraint(
        "ck_election_addendum_requests_finalize_requires_document",
        "election_addendum_requests",
        "finalized_at IS NULL OR document_reference IS NOT NULL",
    )
    op.create_check_constraint(
        "ck_election_addendum_requests_finalize_requires_bfcc_qio",
        "election_addendum_requests",
        "finalized_at IS NULL OR bfcc_qio_information_furnished = true",
    )

    # ---------------------------------------------------------
    # CREATE election_addendum_determinations
    # ---------------------------------------------------------
    op.create_table(
        "election_addendum_determinations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("addendum_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("determination_type", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("relationship_status", sa.String(length=20), nullable=False),
        sa.Column("coverage_status", sa.String(length=20), nullable=False),
        sa.Column("clinical_rationale", sa.Text(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("source_record_type", sa.String(length=50), nullable=True),
        sa.Column("source_record_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["addendum_request_id"],
            ["election_addendum_requests.id"],
            name="fk_election_addendum_determinations_addendum_request_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name="fk_election_addendum_determinations_created_by"
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"], ["users.id"], name="fk_election_addendum_determinations_updated_by"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_election_addendum_determinations"),
        sa.CheckConstraint(
            "relationship_status != 'UNRELATED' OR clinical_rationale IS NOT NULL",
            name="ck_election_addendum_determinations_unrelated_requires_rationale",
        ),
    )
    op.create_index(
        "ix_election_addendum_determinations_tenant_id", "election_addendum_determinations", ["tenant_id"]
    )
    op.create_index(
        "ix_election_addendum_determinations_addendum_request_id",
        "election_addendum_determinations",
        ["addendum_request_id"],
    )

    # ---------------------------------------------------------
    # CREATE election_addendum_audit_events
    # ---------------------------------------------------------
    op.create_table(
        "election_addendum_audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("addendum_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("admission_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("prior_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["addendum_request_id"],
            ["election_addendum_requests.id"],
            name="fk_election_addendum_audit_events_addendum_request_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"], ["patients.id"], name="fk_election_addendum_audit_events_patient_id", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"], ["users.id"], name="fk_election_addendum_audit_events_actor_user_id"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_election_addendum_audit_events"),
        sa.CheckConstraint(
            "event_type IN ("
            "'REQUIREMENT_CREATED','DETERMINATION_RECORDED','ADDENDUM_GENERATED',"
            "'ADDENDUM_FURNISHED','ADDENDUM_ACKNOWLEDGED','ADDENDUM_REFUSED',"
            "'ADDENDUM_SUPERSEDED','DEADLINE_MISSED','RECORD_CORRECTED','RECORD_FINALIZED'"
            ")",
            name="ck_election_addendum_audit_events_type",
        ),
    )
    op.create_index(
        "ix_election_addendum_audit_events_tenant_id", "election_addendum_audit_events", ["tenant_id"]
    )
    op.create_index(
        "ix_election_addendum_audit_events_addendum_request_id",
        "election_addendum_audit_events",
        ["addendum_request_id"],
    )
    op.create_index(
        "ix_election_addendum_audit_events_patient_id", "election_addendum_audit_events", ["patient_id"]
    )
    op.create_index(
        "ix_election_addendum_audit_events_admission_id", "election_addendum_audit_events", ["admission_id"]
    )
    op.create_index(
        "ix_election_addendum_audit_events_event_type", "election_addendum_audit_events", ["event_type"]
    )
    op.create_index(
        "ix_election_addendum_audit_events_correlation_id", "election_addendum_audit_events", ["correlation_id"]
    )
    op.create_index(
        "ix_election_addendum_audit_events_created_at", "election_addendum_audit_events", ["created_at"]
    )
    op.create_index(
        "ix_election_addendum_audit_events_tenant_event_created",
        "election_addendum_audit_events",
        ["tenant_id", "event_type", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("election_addendum_audit_events")
    op.drop_table("election_addendum_determinations")

    op.drop_constraint(
        "ck_election_addendum_requests_finalize_requires_bfcc_qio",
        "election_addendum_requests",
        type_="check",
    )
    op.drop_constraint(
        "ck_election_addendum_requests_finalize_requires_document",
        "election_addendum_requests",
        type_="check",
    )
    op.drop_constraint(
        "ck_election_addendum_requests_refusal_requires_reason",
        "election_addendum_requests",
        type_="check",
    )
    op.drop_constraint(
        "ck_election_addendum_requests_ack_requires_timestamp",
        "election_addendum_requests",
        type_="check",
    )
    op.drop_constraint(
        "ck_election_addendum_requests_no_self_supersede", "election_addendum_requests", type_="check"
    )
    op.drop_constraint(
        "ck_election_addendum_requests_version_positive", "election_addendum_requests", type_="check"
    )
    op.drop_constraint(
        "uq_election_addendum_requests_tenant_admission_version",
        "election_addendum_requests",
        type_="unique",
    )
    op.drop_index("ix_election_addendum_requests_admission_id", table_name="election_addendum_requests")
    op.drop_index("ix_election_addendum_requests_tenant_admission", table_name="election_addendum_requests")
    op.drop_constraint(
        "fk_election_addendum_requests_finalized_by_user_id",
        "election_addendum_requests",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_election_addendum_requests_furnished_by_user_id",
        "election_addendum_requests",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_election_addendum_requests_determined_by_user_id",
        "election_addendum_requests",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_election_addendum_requests_supersedes_request_id",
        "election_addendum_requests",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_election_addendum_requests_admission_id_admissions",
        "election_addendum_requests",
        type_="foreignkey",
    )

    op.drop_column("election_addendum_requests", "finalized_by_user_id")
    op.drop_column("election_addendum_requests", "finalized_at")
    op.drop_column("election_addendum_requests", "document_reference")
    op.drop_column("election_addendum_requests", "bfcc_qio_information_furnished")
    op.drop_column("election_addendum_requests", "refusal_reason")
    op.drop_column("election_addendum_requests", "acknowledged_at")
    op.drop_column("election_addendum_requests", "acknowledgment_status")
    op.drop_column("election_addendum_requests", "delivery_method")
    op.drop_column("election_addendum_requests", "furnished_to_name")
    op.drop_column("election_addendum_requests", "furnished_to_type")
    op.drop_column("election_addendum_requests", "furnished_by_user_id")
    op.drop_column("election_addendum_requests", "furnished_at")
    op.drop_column("election_addendum_requests", "determined_by_account_discipline")
    op.drop_column("election_addendum_requests", "determined_by_user_id")
    op.drop_column("election_addendum_requests", "determination_completed_at")
    op.drop_column("election_addendum_requests", "supersedes_request_id")
    op.drop_column("election_addendum_requests", "version_number")
    op.drop_column("election_addendum_requests", "mandatory_rule_applies")
    op.drop_column("election_addendum_requests", "required_by_at")
    op.drop_column("election_addendum_requests", "election_effective_date")
    op.drop_column("election_addendum_requests", "triggered_at")
    op.drop_column("election_addendum_requests", "trigger_type")
    op.drop_column("election_addendum_requests", "admission_id")

    op.alter_column(
        "election_addendum_requests",
        "requested_by",
        existing_type=sa.String(length=32),
        nullable=False,
    )
    op.alter_column(
        "election_addendum_requests", "requested_date", existing_type=sa.Date(), nullable=False
    )
