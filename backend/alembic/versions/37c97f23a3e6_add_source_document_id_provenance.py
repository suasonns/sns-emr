"""add source_document_id provenance columns

Revision ID: a1b2c3d4e5f6
Revises: d9e8f7a6b5c4
Create Date: 2026-09-04 11:05:00.000000

Adds a nullable source_document_id FK (-> document_records.id) to
patient_facesheet, patient_diagnoses, and diagnosis_sources.

This is the single canonical provenance pointer required so every
automatically-populated facesheet field or diagnosis derived from an
uploaded PDF can be traced back to the exact Patient Chart -> Documents
record it came from. It is NOT a new document store -- it only references
the existing document_records table.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '37c97f23a3e6'
down_revision: Union[str, Sequence[str], None] = 'd9e8f7a6b5c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "patient_facesheet",
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_patient_facesheet_source_document_id",
        "patient_facesheet",
        "document_records",
        ["source_document_id"],
        ["id"],
    )

    op.add_column(
        "patient_diagnoses",
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_patient_diagnoses_source_document_id",
        "patient_diagnoses",
        "document_records",
        ["source_document_id"],
        ["id"],
    )

    op.add_column(
        "diagnosis_sources",
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_diagnosis_sources_source_document_id",
        "diagnosis_sources",
        "document_records",
        ["source_document_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_diagnosis_sources_source_document_id", "diagnosis_sources", type_="foreignkey"
    )
    op.drop_column("diagnosis_sources", "source_document_id")

    op.drop_constraint(
        "fk_patient_diagnoses_source_document_id", "patient_diagnoses", type_="foreignkey"
    )
    op.drop_column("patient_diagnoses", "source_document_id")

    op.drop_constraint(
        "fk_patient_facesheet_source_document_id", "patient_facesheet", type_="foreignkey"
    )
    op.drop_column("patient_facesheet", "source_document_id")
