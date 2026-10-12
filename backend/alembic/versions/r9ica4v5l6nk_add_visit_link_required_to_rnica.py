"""add visit_link_required to rnica_assessments (RNICA-VISIT-LINK-REQUIRED-001)

Deterministic, migration-time cutover distinguishing historical unlinked
RN ICA records (created before the Visit-linking workflow was mandatory)
from current-workflow records, which must obtain a real Visit link before
full completion. Every row that already exists when this migration runs
is set False (an objective database fact, not a guess based on
timestamps or patient identity); every row created afterward defaults to
True via server_default.

Revision ID: r9ica4v5l6nk
Revises: e5f8a2c4b6d9
Create Date: 2026-10-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "r9ica4v5l6nk"
down_revision = "e5f8a2c4b6d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "rnica_assessments",
        sa.Column(
            "visit_link_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    # Explicit, deterministic cutover: every row that already exists at
    # migration time predates the Visit-ID-required current workflow.
    op.execute("UPDATE rnica_assessments SET visit_link_required = false")
    # Any row created after this migration defaults to True going forward.
    op.alter_column(
        "rnica_assessments",
        "visit_link_required",
        server_default=sa.text("true"),
    )


def downgrade() -> None:
    op.drop_column("rnica_assessments", "visit_link_required")
