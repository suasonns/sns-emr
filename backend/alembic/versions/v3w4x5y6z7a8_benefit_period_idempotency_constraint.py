"""Eligibility Traceability Epic Workstream 1: benefit_periods idempotency constraint.

rollover_benefit_period()'s idempotency check (matching an existing row
by tenant_id/patient_id/benefit_type/start_date before inserting a new
one) relies on `.with_for_update()` row locking against ALREADY-EXISTING
rows. Under PostgreSQL READ COMMITTED semantics, a genuinely concurrent
retry of a rollover for a NOT-YET-EXISTING benefit period can still race
past that check: two transactions can each fail to see the other's
brand-new insert (only the specific row a blocked query was waiting on is
re-evaluated on unblock -- new rows are not retroactively added to an
already-planned query), so both proceed to INSERT a duplicate
(tenant_id, patient_id, benefit_type, start_date) benefit period. This
was confirmed via a real two-thread/two-session reproduction in
tests/test_benefit_period_status_events.py::TestConcurrentRolloverSafety.

This migration adds the missing database-level guarantee: a unique
constraint that makes any such race fail loudly with an IntegrityError
instead of silently creating a duplicate, audit-defeating benefit period.
The service layer (app/services/benefit_period_service.py) is updated in
the same commit to catch that IntegrityError, roll back, and re-fetch the
now-committed row -- turning the race into the same idempotent "return
the existing row" behavior the non-concurrent path already has.

Additive only -- no existing column is altered, no existing data is
touched. Assumes no duplicate rows currently exist (true for every
environment this has been deployed to, since duplicates were only ever
possible under this now-fixed race).

Revision ID: v3w4x5y6z7a8
Revises: u2v3w4x5y6z7
Create Date: 2026-09-08
"""

from typing import Sequence, Union

from alembic import op

revision: str = "v3w4x5y6z7a8"
down_revision: Union[str, Sequence[str], None] = "u2v3w4x5y6z7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CONSTRAINT_NAME = "uq_benefit_periods_tenant_patient_type_start"


def upgrade() -> None:
    op.create_unique_constraint(
        CONSTRAINT_NAME,
        "benefit_periods",
        ["tenant_id", "patient_id", "benefit_type", "start_date"],
    )


def downgrade() -> None:
    op.drop_constraint(CONSTRAINT_NAME, "benefit_periods", type_="unique")
