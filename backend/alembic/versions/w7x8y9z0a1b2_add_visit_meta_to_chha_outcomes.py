"""add visit meta (logistics/payroll) fields to chha_visit_outcomes

Revision ID: w7x8y9z0a1b2
Revises: v6w7x8y9z0a1
Create Date: 2026-08-23 10:00:00.000000

RN ICA, MSW ICA, and SC ICA already capture a "Visit Details" block
(type of visit, reason for visit, time in/out, duration, entered by,
staff assigned, care level) so agencies can track visit logistics for
payroll purposes. CHHA visit notes had no equivalent, so this migration
adds the same fields to chha_visit_outcomes.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "w7x8y9z0a1b2"
down_revision = "v6w7x8y9z0a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("chha_visit_outcomes", sa.Column("correction", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("chha_visit_outcomes", sa.Column("type_of_visit", sa.String(length=32), nullable=True))
    op.add_column("chha_visit_outcomes", sa.Column("visit_kind", sa.String(length=32), nullable=True))
    op.add_column("chha_visit_outcomes", sa.Column("visit_kind_specify", sa.String(length=255), nullable=True))
    op.add_column("chha_visit_outcomes", sa.Column("reason_for_visit", sa.String(length=64), nullable=True))
    op.add_column("chha_visit_outcomes", sa.Column("visit_date", sa.String(length=16), nullable=True))
    op.add_column("chha_visit_outcomes", sa.Column("time_in", sa.String(length=16), nullable=True))
    op.add_column("chha_visit_outcomes", sa.Column("time_out", sa.String(length=16), nullable=True))
    op.add_column("chha_visit_outcomes", sa.Column("duration", sa.String(length=32), nullable=True))
    op.add_column("chha_visit_outcomes", sa.Column("entered_by", sa.String(length=255), nullable=True))
    op.add_column("chha_visit_outcomes", sa.Column("staff_assigned", sa.String(length=255), nullable=True))
    op.add_column("chha_visit_outcomes", sa.Column("care_level", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("chha_visit_outcomes", "care_level")
    op.drop_column("chha_visit_outcomes", "staff_assigned")
    op.drop_column("chha_visit_outcomes", "entered_by")
    op.drop_column("chha_visit_outcomes", "duration")
    op.drop_column("chha_visit_outcomes", "time_out")
    op.drop_column("chha_visit_outcomes", "time_in")
    op.drop_column("chha_visit_outcomes", "reason_for_visit")
    op.drop_column("chha_visit_outcomes", "visit_date")
    op.drop_column("chha_visit_outcomes", "visit_kind_specify")
    op.drop_column("chha_visit_outcomes", "visit_kind")
    op.drop_column("chha_visit_outcomes", "type_of_visit")
    op.drop_column("chha_visit_outcomes", "correction")
