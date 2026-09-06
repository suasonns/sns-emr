"""add facesheet_field_suggestions table

Revision ID: b7c3d2e1f0a9
Revises: 37c97f23a3e6
Create Date: 2026-09-04 13:05:00.000000

Adds facesheet_field_suggestions: the reconciliation table for
demographic-field conflicts detected during automated document
ingestion. When an uploaded document's extracted value for an
identity/administrative facesheet field (name, DOB, MRN, gender,
address, phone) conflicts with an existing, already-populated value,
the conflict is recorded here instead of silently overwriting the
facesheet -- a human then accepts or rejects it (audited either way).
This does not affect clinical fields (diagnoses, evidence, RNICA),
which continue to auto-update via the existing evidence/harvester
pipeline.

Also adds tenants.facesheet_protection_mode (OFF / WARN /
REQUIRE_REVIEW, default REQUIRE_REVIEW) -- the tenant-level control for
this behavior.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b7c3d2e1f0a9'
down_revision: Union[str, Sequence[str], None] = '37c97f23a3e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(
            "facesheet_protection_mode",
            sa.String(length=32),
            nullable=False,
            server_default="REQUIRE_REVIEW",
        ),
    )
    op.create_check_constraint(
        "ck_tenant_facesheet_protection_mode_valid",
        "tenants",
        "facesheet_protection_mode IN ('OFF', 'WARN', 'REQUIRE_REVIEW')",
    )

    op.create_table(
        "facesheet_field_suggestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id"),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
        ),
        sa.Column("field_name", sa.String(), nullable=False),
        sa.Column("current_value", sa.String(), nullable=True),
        sa.Column("suggested_value", sa.String(), nullable=True),
        sa.Column(
            "source_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("document_records.id"),
            nullable=True,
        ),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "resolved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_facesheet_field_suggestions_patient_status",
        "facesheet_field_suggestions",
        ["tenant_id", "patient_id", "status"],
    )
    op.create_index(
        "ix_facesheet_field_suggestions_tenant_id",
        "facesheet_field_suggestions",
        ["tenant_id"],
    )
    op.create_index(
        "ix_facesheet_field_suggestions_patient_id",
        "facesheet_field_suggestions",
        ["patient_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_facesheet_field_suggestions_patient_id",
        table_name="facesheet_field_suggestions",
    )
    op.drop_index(
        "ix_facesheet_field_suggestions_tenant_id",
        table_name="facesheet_field_suggestions",
    )
    op.drop_index(
        "ix_facesheet_field_suggestions_patient_status",
        table_name="facesheet_field_suggestions",
    )
    op.drop_table("facesheet_field_suggestions")
    op.drop_constraint(
        "ck_tenant_facesheet_protection_mode_valid", "tenants", type_="check"
    )
    op.drop_column("tenants", "facesheet_protection_mode")
