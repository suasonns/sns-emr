"""restore care_level_snapshot on clinical_notes (lost in consolidation)

Revision ID: u5v6w7x8y9z0
Revises: t4u5v6w7x8y9
Create Date: 2026-08-22 22:15:00.000000

This column was originally added by migration 8bd03327f9df ("add
care_level_snapshot to clinical_notes"). That migration file was deleted
during a later "collapse to one migrations folder" consolidation and was
never folded into the resulting consolidated baseline
(521d501c6eea_consolidated_baseline.py), so the column silently vanished
from the live schema even though app/api/visits.py has continued to pass
care_level_snapshot=... to the ClinicalNote constructor. This migration is
forward-only: it does not rewrite or replace any existing migration, it
simply re-adds the missing column on top of the current head.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "u5v6w7x8y9z0"
down_revision = "t4u5v6w7x8y9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "clinical_notes",
        sa.Column("care_level_snapshot", sa.String(length=20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("clinical_notes", "care_level_snapshot")
