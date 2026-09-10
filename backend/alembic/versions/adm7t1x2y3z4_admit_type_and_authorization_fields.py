"""Admit Type driver + Starting Cert + Transfer fields (Priority 5) and
Contracted/Authorization tri-state fields (Priority 4).

Adds, purely additively:

- benefit_period_determinations.admit_type          (NEW_ADMISSION | READMISSION | TRANSFER_FROM_ANOTHER_HOSPICE)
- benefit_period_determinations.starting_cert        (Integer, staff-entered, never defaulted)
- benefit_period_determinations.transfer_source       (String, Transfer-only)
- benefit_period_determinations.transfer_evidence_document_id (FK -> eligibility_source_documents, Transfer-only)
- patient_facesheet.contracted_status                 (YES | NO | UNKNOWN, staff-reviewed)
- patient_facesheet.authorization_required_status     (YES | NO | UNKNOWN, staff-reviewed)
- patient_facesheet.non_auth_verification_document_id (FK -> eligibility_source_documents)

Per docs/workflows/AdmissionTypesWorkflow.md and SourceOfTruthMatrix.md:
these fields are always staff-entered/staff-reviewed. No default values,
no computed values. All new columns are nullable.

Revision ID: adm7t1x2y3z4
Revises: soc9d8b7a6c5
Create Date: 2026-09-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "adm7t1x2y3z4"
down_revision: Union[str, Sequence[str], None] = "soc9d8b7a6c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "benefit_period_determinations",
        sa.Column("admit_type", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "benefit_period_determinations",
        sa.Column("starting_cert", sa.Integer(), nullable=True),
    )
    op.add_column(
        "benefit_period_determinations",
        sa.Column("transfer_source", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "benefit_period_determinations",
        sa.Column(
            "transfer_evidence_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("eligibility_source_documents.id"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_bpd_admit_type",
        "benefit_period_determinations",
        ["admit_type"],
    )

    op.add_column(
        "patient_facesheet",
        sa.Column("contracted_status", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "patient_facesheet",
        sa.Column("authorization_required_status", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "patient_facesheet",
        sa.Column(
            "non_auth_verification_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("eligibility_source_documents.id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("patient_facesheet", "non_auth_verification_document_id")
    op.drop_column("patient_facesheet", "authorization_required_status")
    op.drop_column("patient_facesheet", "contracted_status")

    op.drop_index("ix_bpd_admit_type", table_name="benefit_period_determinations")
    op.drop_column("benefit_period_determinations", "transfer_evidence_document_id")
    op.drop_column("benefit_period_determinations", "transfer_source")
    op.drop_column("benefit_period_determinations", "starting_cert")
    op.drop_column("benefit_period_determinations", "admit_type")
