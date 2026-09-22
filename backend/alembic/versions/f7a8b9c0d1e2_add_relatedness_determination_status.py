"""Add relatedness-review workflow_status and item-level relatedness
review tracking to election_addendum_requests / election_addendum_determinations

Revision ID: f7a8b9c0d1e2
Revises: d3e4f5a6b7c8
Create Date: 2026-09-21

Workflow-owner decision: the operational risk in the FY2027 mandatory
addendum workflow is DELAYED RELATEDNESS DETERMINATION (dialysis,
specialty medications, transplant-related therapies, unusual DME,
complex coverage determinations requiring physician review) -- not
document finalization. The gap is tracking completion of the
relatedness determination, not building a separate furnish/finalize
workflow.

This migration:

  - Adds election_addendum_requests.workflow_status: REQUIREMENT_CREATED
    (default) -> PENDING_RELATEDNESS_REVIEW -> READY_FOR_GENERATION ->
    ADDENDUM_GENERATED -> ADDENDUM_FURNISHED, with EXCEPTION_CLOSED
    reachable from any open state. Backfilled deterministically from
    existing furnished_at/document_reference state.
  - Adds relatedness-review, physician-review, generation, furnishing,
    acknowledgment, and exception columns to election_addendum_requests,
    consolidating/renaming the prior ad hoc columns added in
    23062ecb4fd9 (determination_completed_at/determined_by_user_id/
    determined_by_account_discipline -> relatedness_determined_at/
    relatedness_determined_by_user_id; furnished_to_type/furnished_to_name/
    delivery_method -> furnished_to/furnishing_method; acknowledged_at/
    refusal_reason -> acknowledgment_at/signature_exception_reason).
  - Extends election_addendum_determinations (the existing item-level
    relatedness/coverage child table -- reused, not duplicated) with
    coverage_owner, current_provider_or_supplier, reviewed_at,
    reviewed_by_user_id, and widens relationship_status to include
    PENDING_REVIEW so the parent's relatedness review can be
    programmatically verified complete.
  - election_addendum_audit_events.actor_account_discipline: brings this
    audit table in line with the other three per-domain audit tables
    (ClinicalOutcomeAuditEvent/IDGReviewAuditEvent/ComplianceAuditEvent).
  - Widens ck_election_addendum_audit_events_type to the full relatedness-
    review event vocabulary.

Deliberately NOT added: a second "relatedness item" table, or a parallel
hospice_election_addendum table.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f7a8b9c0d1e2"
down_revision = "d3e4f5a6b7c8"
branch_labels = None
depends_on = None

OLD_AUDIT_EVENT_CONSTRAINT = (
    "event_type IN ("
    "'REQUIREMENT_CREATED','DETERMINATION_RECORDED','ADDENDUM_GENERATED',"
    "'ADDENDUM_FURNISHED','ADDENDUM_ACKNOWLEDGED','ADDENDUM_REFUSED',"
    "'ADDENDUM_SUPERSEDED','DEADLINE_MISSED','RECORD_CORRECTED','RECORD_FINALIZED'"
    ")"
)

NEW_AUDIT_EVENT_CONSTRAINT = (
    "event_type IN ("
    "'REQUIREMENT_CREATED','RELATEDNESS_REVIEW_STARTED','RELATEDNESS_ITEM_CREATED',"
    "'RELATEDNESS_ITEM_DETERMINED','DETERMINATION_RECORDED','PHYSICIAN_REVIEW_REQUESTED',"
    "'PHYSICIAN_REVIEW_COMPLETED','RELATEDNESS_DETERMINED','RELATEDNESS_REVIEW_COMPLETED',"
    "'ADDENDUM_GENERATED','ADDENDUM_FURNISHED','ACKNOWLEDGMENT_RECORDED','ACKNOWLEDGMENT_REFUSED',"
    "'ADDENDUM_ACKNOWLEDGED','ADDENDUM_REFUSED','ADDENDUM_SUPERSEDED','ADDENDUM_UPDATE_REQUIRED',"
    "'EXCEPTION_RECORDED','DEADLINE_MISSED','RECORD_CORRECTED','RECORD_FINALIZED','RECORD_REOPENED'"
    ")"
)


def upgrade() -> None:
    # ---------------------------------------------------------
    # election_addendum_requests: new workflow_status column
    # ---------------------------------------------------------
    op.add_column(
        "election_addendum_requests",
        sa.Column(
            "workflow_status",
            sa.String(length=40),
            nullable=False,
            server_default="REQUIREMENT_CREATED",
        ),
    )
    # Deterministic backfill from existing state (no rows are expected to
    # exist yet since this table extension is uncommitted/unreleased, but
    # backfill is included for correctness in any environment where the
    # base migration has already run and rows exist).
    op.execute(
        "UPDATE election_addendum_requests SET workflow_status = "
        "CASE "
        "WHEN furnished_at IS NOT NULL THEN 'ADDENDUM_FURNISHED' "
        "WHEN document_reference IS NOT NULL THEN 'ADDENDUM_GENERATED' "
        "ELSE 'REQUIREMENT_CREATED' END"
    )
    op.create_index(
        "ix_election_addendum_requests_workflow_status", "election_addendum_requests", ["workflow_status"]
    )
    op.create_check_constraint(
        "ck_ear_workflow_status",
        "election_addendum_requests",
        "workflow_status IN ("
        "'REQUIREMENT_CREATED','PENDING_RELATEDNESS_REVIEW','READY_FOR_GENERATION',"
        "'ADDENDUM_GENERATED','ADDENDUM_FURNISHED','EXCEPTION_CLOSED'"
        ")",
    )

    # ---------------------------------------------------------
    # election_addendum_requests: relatedness review + physician review
    # ---------------------------------------------------------
    op.add_column(
        "election_addendum_requests",
        sa.Column("relatedness_review_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "election_addendum_requests",
        sa.Column("relatedness_review_started_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "election_addendum_requests", sa.Column("relatedness_review_reason", sa.Text(), nullable=True)
    )
    op.add_column(
        "election_addendum_requests", sa.Column("relatedness_determined_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "election_addendum_requests",
        sa.Column("relatedness_determined_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "election_addendum_requests", sa.Column("clinical_rationale", sa.Text(), nullable=True)
    )
    op.add_column(
        "election_addendum_requests",
        sa.Column("physician_review_required", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "election_addendum_requests",
        sa.Column("physician_review_requested_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "election_addendum_requests",
        sa.Column("physician_reviewer_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "election_addendum_requests", sa.Column("physician_reviewed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "election_addendum_requests", sa.Column("physician_review_rationale", sa.Text(), nullable=True)
    )

    # ---------------------------------------------------------
    # election_addendum_requests: generation / furnishing / ack / exception
    # ---------------------------------------------------------
    op.add_column(
        "election_addendum_requests", sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "election_addendum_requests", sa.Column("document_version", sa.Integer(), nullable=True)
    )
    op.add_column(
        "election_addendum_requests", sa.Column("furnished_to", sa.String(length=40), nullable=True)
    )
    op.add_column(
        "election_addendum_requests", sa.Column("furnishing_method", sa.String(length=40), nullable=True)
    )
    op.alter_column(
        "election_addendum_requests",
        "acknowledgment_status",
        existing_type=sa.String(length=20),
        type_=sa.String(length=40),
    )
    op.add_column(
        "election_addendum_requests", sa.Column("acknowledgment_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "election_addendum_requests", sa.Column("acknowledgment_document_reference", sa.Text(), nullable=True)
    )
    op.add_column(
        "election_addendum_requests", sa.Column("signature_exception_reason", sa.Text(), nullable=True)
    )
    op.add_column(
        "election_addendum_requests", sa.Column("exception_type", sa.String(length=40), nullable=True)
    )
    op.add_column(
        "election_addendum_requests", sa.Column("exception_occurred_at", sa.DateTime(timezone=True), nullable=True)
    )

    # ---- Migrate data from the columns being consolidated, then drop them ----
    op.execute(
        "UPDATE election_addendum_requests SET "
        "relatedness_determined_at = determination_completed_at, "
        "relatedness_determined_by_user_id = determined_by_user_id, "
        "acknowledgment_at = acknowledged_at, "
        "signature_exception_reason = refusal_reason, "
        "furnishing_method = delivery_method, "
        "furnished_to = CASE furnished_to_type "
        "  WHEN 'BENEFICIARY' THEN 'PATIENT' "
        "  WHEN 'REPRESENTATIVE' THEN 'REPRESENTATIVE' "
        "  ELSE furnished_to_type END "
        "WHERE determination_completed_at IS NOT NULL OR determined_by_user_id IS NOT NULL "
        "OR acknowledged_at IS NOT NULL OR refusal_reason IS NOT NULL "
        "OR delivery_method IS NOT NULL OR furnished_to_type IS NOT NULL"
    )

    # NOTE: determination_completed_at / determined_by_user_id /
    # determined_by_account_discipline / furnished_to_type /
    # furnished_to_name / delivery_method / acknowledged_at / refusal_reason
    # are intentionally left in place (deprecated, no longer written by the
    # ORM model or service layer) rather than dropped -- this repository's
    # migration-safety guard (alembic/env.py validate_migration_safety)
    # blocks op.drop_column/op.drop_table/op.drop_index inside upgrade().
    # A future, separately-reviewed cleanup migration may drop them once
    # it is confirmed no code/reporting path still reads them.

    op.create_foreign_key(
        "fk_ear_relatedness_started_by_user",
        "election_addendum_requests",
        "users",
        ["relatedness_review_started_by_user_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_ear_relatedness_determined_by_user",
        "election_addendum_requests",
        "users",
        ["relatedness_determined_by_user_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_ear_physician_reviewer_user",
        "election_addendum_requests",
        "users",
        ["physician_reviewer_user_id"],
        ["id"],
    )

    op.create_check_constraint(
        "ck_ear_furnished_to",
        "election_addendum_requests",
        "furnished_to IS NULL OR furnished_to IN ('PATIENT','REPRESENTATIVE')",
    )
    op.create_check_constraint(
        "ck_ear_furnishing_method",
        "election_addendum_requests",
        "furnishing_method IS NULL OR furnishing_method IN "
        "('IN_PERSON','PAPER_PACKET','ELECTRONIC','MAIL','OTHER')",
    )
    op.create_check_constraint(
        "ck_ear_exception_type",
        "election_addendum_requests",
        "exception_type IS NULL OR exception_type IN "
        "('PATIENT_DIED','ELECTION_REVOKED','PATIENT_DISCHARGED','OTHER_ALLOWED_EXCEPTION')",
    )
    op.create_check_constraint(
        "ck_ear_acknowledgment_status",
        "election_addendum_requests",
        "acknowledgment_status IS NULL OR acknowledgment_status IN ("
        "'PENDING','SIGNED_BY_PATIENT','SIGNED_BY_REPRESENTATIVE','REFUSED',"
        "'UNABLE_TO_SIGN','NOT_REQUIRED_DUE_TO_EXCEPTION'"
        ")",
    )
    op.create_check_constraint(
        "ck_ear_document_version_positive",
        "election_addendum_requests",
        "document_version IS NULL OR document_version > 0",
    )
    op.create_check_constraint(
        "ck_ear_generated_requires_document",
        "election_addendum_requests",
        "workflow_status NOT IN ('ADDENDUM_GENERATED','ADDENDUM_FURNISHED') "
        "OR (document_reference IS NOT NULL AND generated_at IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_ear_furnished_requires_evidence",
        "election_addendum_requests",
        "workflow_status != 'ADDENDUM_FURNISHED' OR ("
        "furnished_at IS NOT NULL AND furnished_to IS NOT NULL AND furnishing_method IS NOT NULL"
        ")",
    )
    op.create_check_constraint(
        "ck_ear_furnished_after_generated",
        "election_addendum_requests",
        "furnished_at IS NULL OR generated_at IS NULL OR furnished_at >= generated_at",
    )
    op.create_check_constraint(
        "ck_ear_exception_requires_evidence",
        "election_addendum_requests",
        "workflow_status != 'EXCEPTION_CLOSED' OR ("
        "exception_type IS NOT NULL AND exception_occurred_at IS NOT NULL"
        ")",
    )
    op.create_check_constraint(
        "ck_ear_ack_requires_timestamp",
        "election_addendum_requests",
        "acknowledgment_status NOT IN ('SIGNED_BY_PATIENT','SIGNED_BY_REPRESENTATIVE','REFUSED','UNABLE_TO_SIGN')"
        " OR acknowledgment_at IS NOT NULL",
    )
    op.create_check_constraint(
        "ck_ear_refusal_requires_reason",
        "election_addendum_requests",
        "acknowledgment_status != 'REFUSED' OR signature_exception_reason IS NOT NULL",
    )

    # ---------------------------------------------------------
    # election_addendum_determinations: item-level relatedness review
    # ---------------------------------------------------------
    op.add_column(
        "election_addendum_determinations",
        sa.Column("coverage_owner", sa.String(length=30), nullable=True),
    )
    op.add_column(
        "election_addendum_determinations",
        sa.Column("current_provider_or_supplier", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "election_addendum_determinations", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "election_addendum_determinations",
        sa.Column("reviewed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.alter_column(
        "election_addendum_determinations",
        "relationship_status",
        existing_type=sa.String(length=20),
        server_default="PENDING_REVIEW",
    )
    op.alter_column(
        "election_addendum_determinations",
        "coverage_status",
        existing_type=sa.String(length=20),
        nullable=True,
    )
    op.create_foreign_key(
        "fk_ead_reviewed_by_user",
        "election_addendum_determinations",
        "users",
        ["reviewed_by_user_id"],
        ["id"],
    )
    op.create_check_constraint(
        "ck_eadetermination_relationship_status",
        "election_addendum_determinations",
        "relationship_status IN ('PENDING_REVIEW','RELATED','UNRELATED')",
    )
    op.create_check_constraint(
        "ck_eadetermination_pending_has_no_review",
        "election_addendum_determinations",
        "relationship_status != 'PENDING_REVIEW' OR (reviewed_at IS NULL AND reviewed_by_user_id IS NULL)",
    )
    op.create_check_constraint(
        "ck_eadetermination_reviewed_requires_actor",
        "election_addendum_determinations",
        "relationship_status = 'PENDING_REVIEW' OR (reviewed_at IS NOT NULL AND reviewed_by_user_id IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_eadetermination_reviewed_requires_coverage_status",
        "election_addendum_determinations",
        "relationship_status = 'PENDING_REVIEW' OR coverage_status IS NOT NULL",
    )

    # ---------------------------------------------------------
    # election_addendum_audit_events: discipline snapshot + widened events
    # ---------------------------------------------------------
    op.add_column(
        "election_addendum_audit_events",
        sa.Column("actor_account_discipline", sa.String(length=50), nullable=True),
    )
    op.drop_constraint(
        "ck_election_addendum_audit_events_type", "election_addendum_audit_events", type_="check"
    )
    op.create_check_constraint(
        "ck_election_addendum_audit_events_type",
        "election_addendum_audit_events",
        NEW_AUDIT_EVENT_CONSTRAINT,
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_election_addendum_audit_events_type", "election_addendum_audit_events", type_="check"
    )
    op.create_check_constraint(
        "ck_election_addendum_audit_events_type",
        "election_addendum_audit_events",
        OLD_AUDIT_EVENT_CONSTRAINT,
    )
    op.drop_column("election_addendum_audit_events", "actor_account_discipline")

    op.drop_constraint(
        "ck_eadetermination_reviewed_requires_coverage_status", "election_addendum_determinations", type_="check"
    )
    op.drop_constraint(
        "ck_eadetermination_reviewed_requires_actor", "election_addendum_determinations", type_="check"
    )
    op.drop_constraint(
        "ck_eadetermination_pending_has_no_review", "election_addendum_determinations", type_="check"
    )
    op.drop_constraint(
        "ck_eadetermination_relationship_status", "election_addendum_determinations", type_="check"
    )
    op.drop_constraint("fk_ead_reviewed_by_user", "election_addendum_determinations", type_="foreignkey")
    op.execute(
        "UPDATE election_addendum_determinations SET coverage_status = 'NOT_COVERED' WHERE coverage_status IS NULL"
    )
    op.alter_column(
        "election_addendum_determinations",
        "coverage_status",
        existing_type=sa.String(length=20),
        nullable=False,
    )
    op.alter_column(
        "election_addendum_determinations",
        "relationship_status",
        existing_type=sa.String(length=20),
        server_default=None,
    )
    op.drop_column("election_addendum_determinations", "reviewed_by_user_id")
    op.drop_column("election_addendum_determinations", "reviewed_at")
    op.drop_column("election_addendum_determinations", "current_provider_or_supplier")
    op.drop_column("election_addendum_determinations", "coverage_owner")

    op.drop_constraint("ck_ear_refusal_requires_reason", "election_addendum_requests", type_="check")
    op.drop_constraint("ck_ear_ack_requires_timestamp", "election_addendum_requests", type_="check")
    op.drop_constraint("ck_ear_exception_requires_evidence", "election_addendum_requests", type_="check")
    op.drop_constraint("ck_ear_furnished_after_generated", "election_addendum_requests", type_="check")
    op.drop_constraint("ck_ear_furnished_requires_evidence", "election_addendum_requests", type_="check")
    op.drop_constraint("ck_ear_generated_requires_document", "election_addendum_requests", type_="check")
    op.drop_constraint("ck_ear_document_version_positive", "election_addendum_requests", type_="check")
    op.drop_constraint("ck_ear_acknowledgment_status", "election_addendum_requests", type_="check")
    op.drop_constraint("ck_ear_exception_type", "election_addendum_requests", type_="check")
    op.drop_constraint("ck_ear_furnishing_method", "election_addendum_requests", type_="check")
    op.drop_constraint("ck_ear_furnished_to", "election_addendum_requests", type_="check")

    op.drop_constraint("fk_ear_physician_reviewer_user", "election_addendum_requests", type_="foreignkey")
    op.drop_constraint("fk_ear_relatedness_determined_by_user", "election_addendum_requests", type_="foreignkey")
    op.drop_constraint("fk_ear_relatedness_started_by_user", "election_addendum_requests", type_="foreignkey")

    # NOTE: determination_completed_at / determined_by_user_id /
    # determined_by_account_discipline / furnished_to_type /
    # furnished_to_name / delivery_method / acknowledged_at / refusal_reason
    # were never dropped in upgrade() (see note there), so there is nothing
    # to restore here.


    op.drop_column("election_addendum_requests", "exception_occurred_at")
    op.drop_column("election_addendum_requests", "exception_type")
    op.drop_column("election_addendum_requests", "signature_exception_reason")
    op.drop_column("election_addendum_requests", "acknowledgment_document_reference")
    op.drop_column("election_addendum_requests", "acknowledgment_at")
    op.alter_column(
        "election_addendum_requests",
        "acknowledgment_status",
        existing_type=sa.String(length=40),
        type_=sa.String(length=20),
    )
    op.drop_column("election_addendum_requests", "furnishing_method")
    op.drop_column("election_addendum_requests", "furnished_to")
    op.drop_column("election_addendum_requests", "document_version")
    op.drop_column("election_addendum_requests", "generated_at")

    op.drop_column("election_addendum_requests", "physician_review_rationale")
    op.drop_column("election_addendum_requests", "physician_reviewed_at")
    op.drop_column("election_addendum_requests", "physician_reviewer_user_id")
    op.drop_column("election_addendum_requests", "physician_review_requested_at")
    op.drop_column("election_addendum_requests", "physician_review_required")
    op.drop_column("election_addendum_requests", "clinical_rationale")
    op.drop_column("election_addendum_requests", "relatedness_determined_by_user_id")
    op.drop_column("election_addendum_requests", "relatedness_determined_at")
    op.drop_column("election_addendum_requests", "relatedness_review_reason")
    op.drop_column("election_addendum_requests", "relatedness_review_started_by_user_id")
    op.drop_column("election_addendum_requests", "relatedness_review_started_at")

    op.drop_constraint("ck_ear_workflow_status", "election_addendum_requests", type_="check")
    op.drop_index("ix_election_addendum_requests_workflow_status", table_name="election_addendum_requests")
    op.drop_column("election_addendum_requests", "workflow_status")
