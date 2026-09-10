"""Payer verification tracking fields on PatientFaceSheet (Priority 4).

Adds, purely additively:

- patient_facesheet.payer_verified_date
- patient_facesheet.payer_verified_by            (FK -> users)
- patient_facesheet.payer_verification_notes
- patient_facesheet.verification_document_reference (FK -> eligibility_source_documents)

IMPORTANT: SNS EMR does not perform eligibility verification itself (no
NGS Connex / CMS / Medicare / payer-database lookup integration -- out of
scope by explicit directive). Staff verify coverage externally and these
fields record who/when/what-evidence backs that external verification;
they support audit only and never perform verification. See
docs/workflows/PayerDeterminationWorkflow.md.

Revision ID: pay3v4e5r6i7f
Revises: ins8f7e6d5c4b
Create Date: 2026-09-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "pay3v4e5r6i7f"
down_revision: Union[str, Sequence[str], None] = "ins8f7e6d5c4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "patient_facesheet",
        sa.Column("payer_verified_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "patient_facesheet",
        sa.Column(
            "payer_verified_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "patient_facesheet",
        sa.Column("payer_verification_notes", sa.String(), nullable=True),
    )
    op.add_column(
        "patient_facesheet",
        sa.Column(
            "verification_document_reference",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("eligibility_source_documents.id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("patient_facesheet", "verification_document_reference")
    op.drop_column("patient_facesheet", "payer_verification_notes")
    op.drop_column("patient_facesheet", "payer_verified_by")
    op.drop_column("patient_facesheet", "payer_verified_date")
