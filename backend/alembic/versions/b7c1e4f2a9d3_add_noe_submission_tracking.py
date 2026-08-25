"""add noe submission tracking to benefit_periods

Revision ID: b7c1e4f2a9d3
Revises: a49295a82a41
Create Date: 2026-08-24

Tracks the real-world Notice of Election (NOE) filing date so the billing
engine can compute CMS's late-NOE non-covered-day penalty (42 CFR
418.24(b)): if the NOE is not filed within 5 calendar days of the start of
hospice care, the days from election start through the day before filing
are non-covered (unless a CMS-recognized exception applies).
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b7c1e4f2a9d3"
down_revision = "a49295a82a41"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "benefit_periods",
        sa.Column("noe_submitted_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "benefit_periods",
        sa.Column("noe_exception_reason", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("benefit_periods", "noe_exception_reason")
    op.drop_column("benefit_periods", "noe_submitted_date")
