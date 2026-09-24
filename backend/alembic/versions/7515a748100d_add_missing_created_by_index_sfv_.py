"""Add missing created_by index on sfv_outcome_corrections

Issue #146 follow-up. `SfvOutcomeCorrection` inherits `BaseModel`, whose
`created_by` column declares `index=True`. The table's own creation
migration (y9z0a1b2c3d4) added the `created_by` column itself but did
not create its index, so CI's autogenerate drift probe (introduced by
main's model-migration-drift reconciliation work) detects the gap.

Purely additive: creates one index. No column/table changes, no data
changes, no J2052C ownership/export/audit logic changes.

Revision ID: 7515a748100d
Revises: f5f4ba60e332
Create Date: 2026-09-24
"""
from alembic import op

revision = "7515a748100d"
down_revision = "f5f4ba60e332"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        op.f("ix_sfv_outcome_corrections_created_by"),
        "sfv_outcome_corrections",
        ["created_by"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_sfv_outcome_corrections_created_by"),
        table_name="sfv_outcome_corrections",
    )
