"""Eligibility, Admission, Benefit-Period, and Billing-Readiness Workflow
Correction -- corrective directive following Sprint 2.

Adds the shared eligibility-source-document / structured-findings /
benefit-period-determination chain (Directive items 3, 4, 6), and widens
two Sprint-2 string columns whose original length caps cannot hold the
corrected code lists (Directive item 10's blocker taxonomy, and the new
ELIGIBILITY_DOCUMENT / ELIGIBILITY_VERIFICATION / BENEFIT_PERIOD_DETERMINATION
/ ADMISSION entity types for the shared audit trail, Directive item 18).
Also adds an additive `evidence_hash` column to `billing_readiness_verdicts`
used to stop duplicate-verdict writes on unchanged evidence (Directive
item 13).

Purely additive -- no existing table is dropped, no existing row is
mutated by this migration; the two ALTER COLUMN TYPE widenings are
non-lossy (VARCHAR(n) -> VARCHAR(m), m > n).

Revision ID: x3y4z5a6b7c8
Revises: w1x2y3z4a5b6
Create Date: 2026-09-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "x3y4z5a6b7c8"
down_revision: Union[str, Sequence[str], None] = "w1x2y3z4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------
    # Widen columns whose corrected code lists no longer fit.
    # ---------------------------------------------------------
    op.alter_column(
        "billing_blocker_records",
        "blocker_code",
        existing_type=sa.String(length=32),
        type_=sa.String(length=48),
        existing_nullable=False,
    )
    op.alter_column(
        "readiness_workflow_events",
        "entity_type",
        existing_type=sa.String(length=16),
        type_=sa.String(length=48),
        existing_nullable=False,
    )

    op.add_column(
        "billing_readiness_verdicts",
        sa.Column("evidence_hash", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_billing_readiness_verdicts_evidence_hash",
        "billing_readiness_verdicts",
        ["evidence_hash"],
    )

    # ---------------------------------------------------------
    # eligibility_source_documents
    # ---------------------------------------------------------
    op.create_table(
        "eligibility_source_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("payer_coverage_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patient_insurances.id"), nullable=True),
        sa.Column("document_record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_records.id"), nullable=False),
        sa.Column("document_type", sa.String(length=48), nullable=False),
        sa.Column("service_date_from", sa.Date(), nullable=True),
        sa.Column("service_date_to", sa.Date(), nullable=True),
        sa.Column("verification_date", sa.Date(), nullable=True),
        sa.Column("uploaded_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("supersedes_document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("eligibility_source_documents.id"), nullable=True),
        sa.Column("status", sa.String(length=16), server_default="ACTIVE", nullable=False),
        sa.Column("parser_status", sa.String(length=16), server_default="UNPARSED", nullable=False),
        sa.Column("parser_version", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_eligibility_source_documents")),
    )
    op.create_index("ix_eligibility_source_documents_tenant_id", "eligibility_source_documents", ["tenant_id"])
    op.create_index("ix_eligibility_source_documents_patient_id", "eligibility_source_documents", ["patient_id"])
    op.create_index("ix_eligibility_source_documents_payer_coverage_id", "eligibility_source_documents", ["payer_coverage_id"])
    op.create_index("ix_eligibility_source_documents_document_record_id", "eligibility_source_documents", ["document_record_id"])
    op.create_index("ix_eligibility_source_documents_document_type", "eligibility_source_documents", ["document_type"])
    op.create_index("ix_eligibility_source_documents_supersedes_document_id", "eligibility_source_documents", ["supersedes_document_id"])
    op.create_index("ix_eligibility_source_documents_status", "eligibility_source_documents", ["status"])
    op.create_index("ix_eligibility_source_documents_parser_status", "eligibility_source_documents", ["parser_status"])
    op.create_index("ix_esd_tenant_patient", "eligibility_source_documents", ["tenant_id", "patient_id"])
    op.create_index("ix_esd_patient_status", "eligibility_source_documents", ["patient_id", "status"])

    op.add_column(
        "billing_blocker_records",
        sa.Column("workflow_owner_category", sa.String(length=16), server_default="BILLER", nullable=False),
    )
    op.add_column(
        "billing_blocker_records",
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("eligibility_source_documents.id"), nullable=True),
    )

    # ---------------------------------------------------------
    # eligibility_verifications
    # ---------------------------------------------------------
    op.create_table(
        "eligibility_verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("payer_coverage_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patient_insurances.id"), nullable=True),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("eligibility_source_documents.id"), nullable=False),
        sa.Column("verification_date", sa.Date(), nullable=True),
        sa.Column("verified_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("verification_method", sa.String(length=32), server_default="MANUAL_ENTRY", nullable=False),
        sa.Column("response_reference", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=24), server_default="NOT_RUN", nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("termination_date", sa.Date(), nullable=True),
        sa.Column("entitlement_data", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("payment_routing_data", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("hospice_utilization_data", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_eligibility_verifications")),
    )
    op.create_index("ix_eligibility_verifications_tenant_id", "eligibility_verifications", ["tenant_id"])
    op.create_index("ix_eligibility_verifications_patient_id", "eligibility_verifications", ["patient_id"])
    op.create_index("ix_eligibility_verifications_payer_coverage_id", "eligibility_verifications", ["payer_coverage_id"])
    op.create_index("ix_eligibility_verifications_source_document_id", "eligibility_verifications", ["source_document_id"])
    op.create_index("ix_eligibility_verifications_status", "eligibility_verifications", ["status"])
    op.create_index("ix_ev_tenant_patient", "eligibility_verifications", ["tenant_id", "patient_id"])
    op.create_index("ix_ev_patient_status", "eligibility_verifications", ["patient_id", "status"])

    # ---------------------------------------------------------
    # benefit_period_determinations
    # ---------------------------------------------------------
    op.create_table(
        "benefit_period_determinations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("admission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("admissions.id"), nullable=True),
        sa.Column("eligibility_verification_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("eligibility_verifications.id"), nullable=True),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("eligibility_source_documents.id"), nullable=True),
        sa.Column("prior_hospice_episode_count", sa.Integer(), nullable=True),
        sa.Column("benefit_periods_used", sa.Integer(), nullable=True),
        sa.Column("anticipated_benefit_period_number", sa.Integer(), nullable=True),
        sa.Column("anticipated_period_start_date", sa.Date(), nullable=True),
        sa.Column("anticipated_period_end_date", sa.Date(), nullable=True),
        sa.Column("face_to_face_applicability", sa.Boolean(), nullable=True),
        sa.Column("determination_status", sa.String(length=32), server_default="NOT_REVIEWED", nullable=False),
        sa.Column("determined_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("determined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("conflict_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("benefit_period_determinations.id"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_benefit_period_determinations")),
    )
    op.create_index("ix_benefit_period_determinations_tenant_id", "benefit_period_determinations", ["tenant_id"])
    op.create_index("ix_benefit_period_determinations_patient_id", "benefit_period_determinations", ["patient_id"])
    op.create_index("ix_benefit_period_determinations_admission_id", "benefit_period_determinations", ["admission_id"])
    op.create_index("ix_benefit_period_determinations_eligibility_verification_id", "benefit_period_determinations", ["eligibility_verification_id"])
    op.create_index("ix_benefit_period_determinations_source_document_id", "benefit_period_determinations", ["source_document_id"])
    op.create_index("ix_benefit_period_determinations_determination_status", "benefit_period_determinations", ["determination_status"])
    op.create_index("ix_benefit_period_determinations_superseded_by_id", "benefit_period_determinations", ["superseded_by_id"])
    op.create_index("ix_bpd_tenant_patient", "benefit_period_determinations", ["tenant_id", "patient_id"])
    op.create_index("ix_bpd_admission", "benefit_period_determinations", ["admission_id"])
    op.create_index("ix_bpd_patient_status", "benefit_period_determinations", ["patient_id", "determination_status"])


def downgrade() -> None:
    op.drop_column("billing_blocker_records", "source_document_id")
    op.drop_column("billing_blocker_records", "workflow_owner_category")

    op.drop_table("benefit_period_determinations")
    op.drop_table("eligibility_verifications")
    op.drop_table("eligibility_source_documents")

    op.drop_index("ix_billing_readiness_verdicts_evidence_hash", table_name="billing_readiness_verdicts")
    op.drop_column("billing_readiness_verdicts", "evidence_hash")

    # NOTE: `readiness_workflow_events.entity_type` is intentionally left at
    # VARCHAR(48) on downgrade rather than narrowed back to VARCHAR(16).
    # eligibility_workflow_service.py writes real entity types up to 29
    # characters (e.g. "BENEFIT_PERIOD_DETERMINATION"); narrowing this
    # column back to 16 is lossy/unsafe against any real data already
    # written under the wider type and previously caused
    # StringDataRightTruncation failures when downgrading past this
    # revision. See app/billing/models/readiness_workflow_event.py.
    op.alter_column(
        "billing_blocker_records",
        "blocker_code",
        existing_type=sa.String(length=48),
        type_=sa.String(length=32),
        existing_nullable=False,
    )
