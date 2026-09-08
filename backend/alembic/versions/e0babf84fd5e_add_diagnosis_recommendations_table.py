"""add diagnosis_recommendations table

Revision ID: e0babf84fd5e
Revises: c8e6e7eef2d6
Create Date: 2026-09-14 00:00:00.000000

VERIFIED PRODUCTION DEFECT FIX (not new feature work): `diagnosis_recommendations`
is read/written via raw SQL by
`app/services/reasoning_result_to_recommendation_service.py`
(ReasoningResultToRecommendationService), which is already invoked -- for
real, on every RN/LVN visit finalize, MSW/SC ICA lock, MD/NP F2F finalize,
and Certification (CTI) signature -- via
`app/services/clinical_reasoning_bridge.py::run_clinical_reasoning()`. No
migration ever created this table, so every one of those call sites would
raise `psycopg2.errors.UndefinedTable` the first time it executed (verified
against the dev DB: the table did not exist). This migration adds exactly
the table `_insert_recommendation()`/`_recommendation_exists()`/
`_load_candidate_reasoning_results()` (indirectly, via `reasoning_result_id`)
already assume, using the exact column list from those raw-SQL statements.
This converts the recommendation engine's write path from
crash-on-first-use into working, tested, existing "read/normalize/evaluate/
explain/recommend" behavior -- it does NOT write patient_diagnoses,
certifications, or any other authoritative record (recommendation_status
starts PENDING_REVIEW; promotion/acceptance is a separate, human-gated
workflow via the reviewed_by/accepted_by/rejected_by/promoted_patient_diagnosis_id
columns, none of which this migration or the writer service populates).

Also creates the optional `diagnosis_recommendation_reasoning_links` join
table that `_insert_reasoning_links_if_supported()` already probes for via
`inspector.has_table(...)` and silently skips when absent -- adding it here
makes the reasoning-result provenance links (which reasoning results backed
a given recommendation) actually persist instead of being silently dropped.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e0babf84fd5e"
down_revision = "c8e6e7eef2d6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "diagnosis_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reasoning_result_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recommendation_source", sa.String(length=100), nullable=False),
        sa.Column("diagnosis_type", sa.String(length=50), nullable=False),
        sa.Column("recommended_status", sa.String(length=50), nullable=False),
        sa.Column("recommendation_status", sa.String(length=50), nullable=False, server_default="PENDING_REVIEW"),
        sa.Column("diagnosis_keyword", sa.String(length=255), nullable=True),
        sa.Column("confidence", sa.String(length=50), nullable=True),
        sa.Column("priority_score", sa.Integer(), nullable=True),
        sa.Column("is_terminal_candidate", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_related_to_terminal_candidate", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("supporting_evidence_summary", sa.Text(), nullable=True),
        sa.Column("clinical_rationale", sa.Text(), nullable=True),
        sa.Column("audit_rationale", sa.Text(), nullable=True),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_document_name", sa.String(length=255), nullable=True),
        sa.Column("requires_rn_review", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("requires_md_review", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("requires_idg_review", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("promoted_patient_diagnosis_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reasoning_version", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("recommendation_group_key", sa.String(length=512), nullable=False),
    )
    op.create_index(
        "ix_diagnosis_recommendations_patient_id",
        "diagnosis_recommendations",
        ["patient_id"],
    )
    op.create_index(
        "ix_diagnosis_recommendations_tenant_id",
        "diagnosis_recommendations",
        ["tenant_id"],
    )
    op.create_unique_constraint(
        "uq_diagnosis_recommendations_patient_group_key",
        "diagnosis_recommendations",
        ["patient_id", "recommendation_group_key"],
    )

    op.create_table(
        "diagnosis_recommendation_reasoning_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "diagnosis_recommendation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("diagnosis_recommendations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reasoning_result_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_diagnosis_recommendation_reasoning_links_recommendation_id",
        "diagnosis_recommendation_reasoning_links",
        ["diagnosis_recommendation_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_diagnosis_recommendation_reasoning_links_recommendation_id",
        table_name="diagnosis_recommendation_reasoning_links",
    )
    op.drop_table("diagnosis_recommendation_reasoning_links")
    op.drop_constraint(
        "uq_diagnosis_recommendations_patient_group_key",
        "diagnosis_recommendations",
        type_="unique",
    )
    op.drop_index("ix_diagnosis_recommendations_tenant_id", table_name="diagnosis_recommendations")
    op.drop_index("ix_diagnosis_recommendations_patient_id", table_name="diagnosis_recommendations")
    op.drop_table("diagnosis_recommendations")
