"""add contact harvesting attribution + patient_contact_suggestions

Revision ID: d2e3f4a5b6c7
Revises: c1d4e5f6a7b8
Create Date: 2026-09-04 16:30:00.000000

Phase 1 of the Task 4A admission-data architecture roadmap: bring
PatientContact up to the same source-attribution/manual-override/review
maturity already proven for PatientDiagnosis/Certification/BenefitPeriod,
and add the GUARDIAN/CONSERVATOR roles + email/preferred-contact fields
called for by the contact audit. patient_contact_suggestions mirrors
facesheet_field_suggestions' pending/accepted/rejected/dismissed review
pattern, scoped to contact roles/fields instead of facesheet demographics.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'd2e3f4a5b6c7'
down_revision: Union[str, Sequence[str], None] = 'c1d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("patient_contacts", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column(
        "patient_contacts",
        sa.Column("is_preferred", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "patient_contacts",
        sa.Column(
            "attribution_source",
            sa.String(length=32),
            nullable=False,
            server_default="MANUAL",
        ),
    )
    op.add_column(
        "patient_contacts",
        sa.Column(
            "source_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("document_records.id"),
            nullable=True,
        ),
    )
    op.add_column("patient_contacts", sa.Column("source_document_name", sa.String(length=255), nullable=True))
    op.add_column("patient_contacts", sa.Column("source_document_page", sa.Integer(), nullable=True))
    op.add_column("patient_contacts", sa.Column("extraction_timestamp", sa.DateTime(timezone=True), nullable=True))
    op.add_column("patient_contacts", sa.Column("extractor_version", sa.String(length=64), nullable=True))
    op.add_column(
        "patient_contacts",
        sa.Column("manual_override", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "patient_contacts",
        sa.Column(
            "manual_override_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )
    op.add_column("patient_contacts", sa.Column("manual_override_at", sa.DateTime(timezone=True), nullable=True))

    # Any pre-existing row was written through the manual set-contact
    # endpoint (harvesting did not exist before this migration) --
    # attribute it correctly rather than leaving a false "MANUAL" default
    # that would be indistinguishable from truly-untouched new rows.
    op.execute(
        "UPDATE patient_contacts SET attribution_source = 'MANUAL' WHERE attribution_source IS NULL"
    )

    op.create_table(
        "patient_contact_suggestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("field_name", sa.String(length=64), nullable=False),
        sa.Column("current_value", sa.String(), nullable=True),
        sa.Column("suggested_value", sa.String(), nullable=True),
        sa.Column(
            "source_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("document_records.id"),
            nullable=True,
        ),
        sa.Column("source_document_name", sa.String(length=255), nullable=True),
        sa.Column("source_document_page", sa.Integer(), nullable=True),
        sa.Column("extractor_version", sa.String(length=64), nullable=True),
        sa.Column("extraction_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    )

    op.create_index(
        "ix_patient_contact_suggestions_patient_status",
        "patient_contact_suggestions",
        ["tenant_id", "patient_id", "status"],
    )
    op.create_index(
        "ix_patient_contact_suggestions_patient_role",
        "patient_contact_suggestions",
        ["patient_id", "role"],
    )
    op.create_index(
        "ix_patient_contact_suggestions_tenant_id",
        "patient_contact_suggestions",
        ["tenant_id"],
    )
    op.create_index(
        "ix_patient_contact_suggestions_patient_id",
        "patient_contact_suggestions",
        ["patient_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_patient_contact_suggestions_patient_id", table_name="patient_contact_suggestions")
    op.drop_index("ix_patient_contact_suggestions_tenant_id", table_name="patient_contact_suggestions")
    op.drop_index("ix_patient_contact_suggestions_patient_role", table_name="patient_contact_suggestions")
    op.drop_index("ix_patient_contact_suggestions_patient_status", table_name="patient_contact_suggestions")
    op.drop_table("patient_contact_suggestions")

    op.drop_column("patient_contacts", "manual_override_at")
    op.drop_column("patient_contacts", "manual_override_by")
    op.drop_column("patient_contacts", "manual_override")
    op.drop_column("patient_contacts", "extractor_version")
    op.drop_column("patient_contacts", "extraction_timestamp")
    op.drop_column("patient_contacts", "source_document_page")
    op.drop_column("patient_contacts", "source_document_name")
    op.drop_column("patient_contacts", "source_document_id")
    op.drop_column("patient_contacts", "attribution_source")
    op.drop_column("patient_contacts", "is_preferred")
    op.drop_column("patient_contacts", "email")
