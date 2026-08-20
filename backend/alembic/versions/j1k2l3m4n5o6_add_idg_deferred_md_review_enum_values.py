"""add IDG_DEFERRED_MD_REVIEW task/completion enum values

Revision ID: j1k2l3m4n5o6
Revises: i0j1k2l3m4n5
Create Date: 2026-08-19
"""
from alembic import op

revision = "j1k2l3m4n5o6"
down_revision = "i0j1k2l3m4n5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside the same transaction that
    # uses the new value — commit first, run it standalone, then resume.
    op.execute("COMMIT")
    op.execute("ALTER TYPE tasktype ADD VALUE IF NOT EXISTS 'IDG_DEFERRED_MD_REVIEW'")
    op.execute("ALTER TYPE completionreferencetype ADD VALUE IF NOT EXISTS 'IDG_PATIENT_REVIEW'")
    op.execute("BEGIN")


def downgrade() -> None:
    # Postgres does not support removing enum values in place; no-op.
    pass
