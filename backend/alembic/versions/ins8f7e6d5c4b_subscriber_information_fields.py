"""Subscriber Information fields on PatientFaceSheet (Priority 3).

Adds, purely additively:

- patient_facesheet.subscriber_name          (String, staff-entered / staff-reviewed)
- patient_facesheet.subscriber_relationship  (String, staff-entered / staff-reviewed)
- patient_facesheet.subscriber_id            (String, staff-entered / staff-reviewed)

Per docs/architecture/InsuranceMappingReconciliation.md: Subscriber
Information had no prior persisted column anywhere in the schema.
PatientFaceSheet remains the single source of truth for all insurance
fields (MBI, Payer, Policy Number, Subscriber Information) -- no new
table is introduced. These columns may be populated by direct staff
entry or by accepting a FacesheetFieldSuggestion (OCR candidate + staff
review); OCR/automation never writes them directly.

Revision ID: ins8f7e6d5c4b
Revises: adm7t1x2y3z4
Create Date: 2026-09-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "ins8f7e6d5c4b"
down_revision: Union[str, Sequence[str], None] = "adm7t1x2y3z4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "patient_facesheet",
        sa.Column("subscriber_name", sa.String(), nullable=True),
    )
    op.add_column(
        "patient_facesheet",
        sa.Column("subscriber_relationship", sa.String(), nullable=True),
    )
    op.add_column(
        "patient_facesheet",
        sa.Column("subscriber_id", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("patient_facesheet", "subscriber_id")
    op.drop_column("patient_facesheet", "subscriber_relationship")
    op.drop_column("patient_facesheet", "subscriber_name")
