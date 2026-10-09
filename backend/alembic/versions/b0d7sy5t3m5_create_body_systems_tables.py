"""Create body_systems_assessments, system_assessments, and review_exceptions

Body Systems Respiratory proof-of-pattern milestone (specification section
19, "Third recommended GitHub task"). Creates the three persistence tables
backing `app/models/body_systems.py` / the frontend domain types in
`src/domain/body-systems/types.ts`:

  - body_systems_assessments: one row per visit's Body Systems assessment.
  - system_assessments: one row per body system per assessment (unique on
    (body_systems_assessment_id, system)); per-system verified clinical
    field values live in its JSONB `data` column, following the same
    "whole-form JSONB blob" convention already used by
    rnica_assessments.form_data.
  - review_exceptions: relational (not JSONB) so open exceptions can be
    queried/filtered by type, status, and blocking level across the
    worklist independently of which system/assessment they belong to.

Purely additive: three brand-new tables, no existing table/column/
constraint/enum is modified, dropped, or backfilled. Forward-only.

Revision ID: b0d7sy5t3m5
Revises: f3a7c1d9e2b4
Create Date: 2026-10-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b0d7sy5t3m5"
down_revision: Union[str, Sequence[str], None] = "f3a7c1d9e2b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BODY_SYSTEM_CODES = (
    "neurological",
    "respiratory",
    "cardiovascular",
    "nutrition",
    "gastrointestinal",
    "genitourinary",
    "musculoskeletal",
    "integumentary",
    "infection_immunological",
    "endocrine",
)
VISIT_MODES = ("admission_comprehensive", "routine_rn", "recertification")
ASSESSMENT_STATUSES = ("draft", "ready_for_review", "recorded", "signed")
ASSESSMENT_SITUATIONS = ("no_current_concern", "stable_existing", "new_or_worsening", "unable_to_assess")
REVIEW_STATES = ("not_reviewed", "in_progress", "reviewed", "reviewed_with_exception")
EXCEPTION_TYPES = (
    "unreviewed_system",
    "required_field_missing",
    "partial_scope",
    "unable_to_assess",
    "source_missing",
    "date_time_missing",
    "conflicting_evidence",
    "nurse_judgment_required",
    "low_confidence_ai",
    "follow_up_missing",
)
EXCEPTION_BLOCKING_LEVELS = ("informational", "draft_allowed", "record_blocking", "signature_blocking")
EXCEPTION_STATUSES = ("open", "resolved", "waived")


def _in_list(values: Sequence[str]) -> str:
    return ", ".join(f"'{value}'" for value in values)


def upgrade() -> None:
    op.create_table(
        "body_systems_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column(
            "patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("visit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("visits.id", ondelete="SET NULL"), nullable=True),
        sa.Column("visit_mode", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(f"visit_mode IN ({_in_list(VISIT_MODES)})", name="ck_body_systems_assessments_visit_mode"),
        sa.CheckConstraint(f"status IN ({_in_list(ASSESSMENT_STATUSES)})", name="ck_body_systems_assessments_status"),
    )
    op.create_index("ix_body_systems_assessments_tenant_id", "body_systems_assessments", ["tenant_id"])
    op.create_index("ix_body_systems_assessments_patient_id", "body_systems_assessments", ["patient_id"])
    op.create_index("ix_body_systems_assessments_visit_id", "body_systems_assessments", ["visit_id"])

    op.create_table(
        "system_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column(
            "body_systems_assessment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("body_systems_assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("system", sa.String(length=32), nullable=False),
        sa.Column("situation", sa.String(length=32), nullable=True),
        sa.Column("review_state", sa.String(length=32), nullable=False, server_default="not_reviewed"),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assessed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("limitation_scope", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("limitation_reason", sa.Text(), nullable=True),
        sa.Column("limitation_assessed_portion", sa.Text(), nullable=True),
        sa.Column("limitation_follow_up_required", sa.Text(), nullable=True),
        sa.Column(
            "data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint(
            "body_systems_assessment_id", "system", name="uq_system_assessments_assessment_system"
        ),
        sa.CheckConstraint(f"system IN ({_in_list(BODY_SYSTEM_CODES)})", name="ck_system_assessments_system"),
        sa.CheckConstraint(
            f"situation IS NULL OR situation IN ({_in_list(ASSESSMENT_SITUATIONS)})",
            name="ck_system_assessments_situation",
        ),
        sa.CheckConstraint(f"review_state IN ({_in_list(REVIEW_STATES)})", name="ck_system_assessments_review_state"),
    )
    op.create_index("ix_system_assessments_tenant_id", "system_assessments", ["tenant_id"])
    op.create_index(
        "ix_system_assessments_body_systems_assessment_id", "system_assessments", ["body_systems_assessment_id"]
    )

    op.create_table(
        "review_exceptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column(
            "body_systems_assessment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("body_systems_assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("system", sa.String(length=32), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("field_path", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("blocking_level", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(f"system IN ({_in_list(BODY_SYSTEM_CODES)})", name="ck_review_exceptions_system"),
        sa.CheckConstraint(f"type IN ({_in_list(EXCEPTION_TYPES)})", name="ck_review_exceptions_type"),
        sa.CheckConstraint(
            f"blocking_level IN ({_in_list(EXCEPTION_BLOCKING_LEVELS)})", name="ck_review_exceptions_blocking_level"
        ),
        sa.CheckConstraint(f"status IN ({_in_list(EXCEPTION_STATUSES)})", name="ck_review_exceptions_status"),
        sa.CheckConstraint(
            "status = 'open' OR resolved_at IS NOT NULL",
            name="ck_review_exceptions_resolved_has_timestamp",
        ),
    )
    op.create_index("ix_review_exceptions_tenant_id", "review_exceptions", ["tenant_id"])
    op.create_index("ix_review_exceptions_body_systems_assessment_id", "review_exceptions", ["body_systems_assessment_id"])


def downgrade() -> None:
    op.drop_index("ix_review_exceptions_body_systems_assessment_id", table_name="review_exceptions")
    op.drop_index("ix_review_exceptions_tenant_id", table_name="review_exceptions")
    op.drop_table("review_exceptions")

    op.drop_index("ix_system_assessments_body_systems_assessment_id", table_name="system_assessments")
    op.drop_index("ix_system_assessments_tenant_id", table_name="system_assessments")
    op.drop_table("system_assessments")

    op.drop_index("ix_body_systems_assessments_visit_id", table_name="body_systems_assessments")
    op.drop_index("ix_body_systems_assessments_patient_id", table_name="body_systems_assessments")
    op.drop_index("ix_body_systems_assessments_tenant_id", table_name="body_systems_assessments")
    op.drop_table("body_systems_assessments")
