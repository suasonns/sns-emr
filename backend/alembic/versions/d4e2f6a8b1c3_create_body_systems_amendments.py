"""create body_systems_amendments table

Body Systems correction/amendment infrastructure (compliance remediation,
application blocker A). Mirrors the SECTION 12 `rnica_amendments`
"never destroy, always append" guarantee -- the same precedent already
followed for `sfv_outcome_corrections` when an entity other than a locked
RN ICA assessment needed this protection. See
app/models/body_systems_amendment.py for the documented reasoning for why
this is a new sibling table rather than a generalization of the existing,
already-shipped `rnica_amendments` table.

Additive migration only; does not modify any existing table, column, or
data. Forward-only.

Revision ID: d4e2f6a8b1c3
Revises: c3b1d9e0f4a7
Create Date: 2026-10-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d4e2f6a8b1c3"
down_revision: Union[str, Sequence[str], None] = "c3b1d9e0f4a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "body_systems_amendments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "system_assessment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("system_assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("system", sa.String(32), nullable=False),
        sa.Column("field_reference", sa.String(128), nullable=True),
        sa.Column("amendment_category", sa.String(32), nullable=False),
        sa.Column("reason_code", sa.String(32), nullable=False),
        sa.Column("requested_change", sa.Text(), nullable=False),
        sa.Column("original_value_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("proposed_value", postgresql.JSONB(), nullable=True),
        sa.Column("request_source", sa.String(16), nullable=False, server_default=sa.text("'STAFF'")),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("decision_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("decision_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_body_systems_amendments_tenant_id", "body_systems_amendments", ["tenant_id"])
    op.create_index("ix_body_systems_amendments_patient_id", "body_systems_amendments", ["patient_id"])
    op.create_index(
        "ix_body_systems_amendments_system_assessment_id", "body_systems_amendments", ["system_assessment_id"]
    )
    op.create_index("ix_body_systems_amendments_system", "body_systems_amendments", ["system"])
    op.create_index("ix_body_systems_amendments_amendment_category", "body_systems_amendments", ["amendment_category"])
    op.create_index("ix_body_systems_amendments_status", "body_systems_amendments", ["status"])
    op.create_index("ix_body_systems_amendments_created_by", "body_systems_amendments", ["created_by"])
    op.create_index(
        "ix_body_systems_amendments_assessment_status",
        "body_systems_amendments",
        ["system_assessment_id", "status"],
    )
    op.create_index(
        "ix_body_systems_amendments_patient_status",
        "body_systems_amendments",
        ["patient_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_body_systems_amendments_patient_status", table_name="body_systems_amendments")
    op.drop_index("ix_body_systems_amendments_assessment_status", table_name="body_systems_amendments")
    op.drop_index("ix_body_systems_amendments_created_by", table_name="body_systems_amendments")
    op.drop_index("ix_body_systems_amendments_status", table_name="body_systems_amendments")
    op.drop_index("ix_body_systems_amendments_amendment_category", table_name="body_systems_amendments")
    op.drop_index("ix_body_systems_amendments_system", table_name="body_systems_amendments")
    op.drop_index("ix_body_systems_amendments_system_assessment_id", table_name="body_systems_amendments")
    op.drop_index("ix_body_systems_amendments_patient_id", table_name="body_systems_amendments")
    op.drop_index("ix_body_systems_amendments_tenant_id", table_name="body_systems_amendments")
    op.drop_table("body_systems_amendments")
