"""Add benefit_period_id FK to election_addendum_requests

Revision ID: 3fa1b52c68d4
Revises: f5ed0b859dcf
Create Date: 2026-09-22

There is no FK from admissions to benefit_periods (benefit_periods is
patient_id-scoped, not admission_id-scoped), so which benefit_periods row
supplied election_effective_date must be recorded explicitly and
auditably -- never re-derived by silent lookup at read time. Confirmed
with workflow owner: election_effective_date is sourced ONLY from
benefit_periods.election_date (the patient's INITIAL benefit period),
never from admissions.election_signed_at, and there is no fallback
between the two.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "3fa1b52c68d4"
down_revision = "f5ed0b859dcf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "election_addendum_requests",
        sa.Column("benefit_period_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_election_addendum_requests_benefit_period_id",
        "election_addendum_requests",
        "benefit_periods",
        ["benefit_period_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_election_addendum_requests_benefit_period_id",
        "election_addendum_requests",
        ["benefit_period_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_election_addendum_requests_benefit_period_id", table_name="election_addendum_requests")
    op.drop_constraint(
        "fk_election_addendum_requests_benefit_period_id",
        "election_addendum_requests",
        type_="foreignkey",
    )
    op.drop_column("election_addendum_requests", "benefit_period_id")
