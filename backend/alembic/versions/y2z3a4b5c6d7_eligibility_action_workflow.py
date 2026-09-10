"""Eligibility action workflow -- Phases A/B operational fields.

Adds the fields the operational upload/reverification actions need on
top of the read-only Phases 1-4 tables (x3y4z5a6b7c8), purely additive:

  eligibility_source_documents.notes    -- free-text notes at upload time
  eligibility_source_documents.version  -- 1-based version number within
                                            a supersession chain (kept as
                                            an explicit column so callers
                                            don't have to walk the
                                            supersedes_document_id chain
                                            to know "which version is
                                            this")
  eligibility_verifications.notes                 -- reverification notes
  eligibility_verifications.coverage_change_flag  -- Phase C impact input
  eligibility_verifications.payer_change_flag     -- Phase C impact input
  eligibility_verifications.msp_change_flag       -- Phase C impact input
  eligibility_verifications.ma_change_flag        -- Phase C impact input
  eligibility_verifications.overlap_concern_flag  -- Phase C impact input

No existing table is dropped or mutated; every new column is nullable or
has a safe server_default so existing rows (and existing Sprint 1/Sprint
2 code paths) are unaffected.

Revision ID: y2z3a4b5c6d7
Revises: x3y4z5a6b7c8
Create Date: 2026-09-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "y2z3a4b5c6d7"
down_revision: Union[str, Sequence[str], None] = "x3y4z5a6b7c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "eligibility_source_documents",
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "eligibility_source_documents",
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    )

    op.add_column(
        "eligibility_verifications",
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "eligibility_verifications",
        sa.Column("coverage_change_flag", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "eligibility_verifications",
        sa.Column("payer_change_flag", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "eligibility_verifications",
        sa.Column("msp_change_flag", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "eligibility_verifications",
        sa.Column("ma_change_flag", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "eligibility_verifications",
        sa.Column("overlap_concern_flag", sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("eligibility_verifications", "overlap_concern_flag")
    op.drop_column("eligibility_verifications", "ma_change_flag")
    op.drop_column("eligibility_verifications", "msp_change_flag")
    op.drop_column("eligibility_verifications", "payer_change_flag")
    op.drop_column("eligibility_verifications", "coverage_change_flag")
    op.drop_column("eligibility_verifications", "notes")

    op.drop_column("eligibility_source_documents", "version")
    op.drop_column("eligibility_source_documents", "notes")
