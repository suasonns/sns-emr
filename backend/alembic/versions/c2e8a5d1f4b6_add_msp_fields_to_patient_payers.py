"""add msp fields to patient_payers

Revision ID: c2e8a5d1f4b6
Revises: b7c1e4f2a9d3
Create Date: 2026-08-24

Adds real Medicare Secondary Payer (MSP) claim-sequencing fields so the
837I payer sequence (SBR01 P/S/T) is derived from actual coordination-of-
benefits data instead of always assuming Medicare is primary.

msp_type_code: CMS-standard MSP value code (e.g. "12" Working Aged/GHP,
"13" ESRD, "14" No-Fault, "15" Workers' Comp, "16" PHS/Other, "41" Black
Lung, "42" VA, "43" Disabled/LGHP, "47" Liability). NULL means this payer
is not an MSP-type payer (e.g. it IS Medicare, or a plain secondary payer
with no MSP relationship to Medicare).

priority_order: explicit COB sequence (1=primary, 2=secondary,
3=tertiary...). Distinct from the pre-existing is_primary boolean, which
cannot represent a 3+ payer sequence or disambiguate conflicting flags.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c2e8a5d1f4b6"
down_revision = "b7c1e4f2a9d3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "patient_payers",
        sa.Column("msp_type_code", sa.String(length=2), nullable=True),
    )
    op.add_column(
        "patient_payers",
        sa.Column("priority_order", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("patient_payers", "priority_order")
    op.drop_column("patient_payers", "msp_type_code")
