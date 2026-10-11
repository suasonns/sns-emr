"""Merge: reconcile Respiratory RNICA-scoping lineage with amendments lineage

Reconciles the two migration branches that independently forked off
`b0d7sy5t3m5` (create_body_systems_tables):

  - `c1e2a3b4d5f6` (this worktree): adds the nullable
    `body_systems_assessments.rnica_assessment_id` FK + index needed by the
    RNICA-assessment-scoped Respiratory route.
  - `d4e2f6a8b1c3` (sibling worktree, already applied to the shared
    development database): adds `system_assessments.limitation_*`
    destination columns (via `c3b1d9e0f4a7`) and the `body_systems_amendments`
    table.

Neither branch's migrations touch a table or column the other branch
touches, so this merge recreates nothing: it is a pure Alembic graph
join plus one guarded, additive data backfill.

Backfill rule (product-owner approved): for each existing
`body_systems_assessments` row, set `rnica_assessment_id` only when
exactly one `rnica_assessments` row shares the same `(patient_id,
visit_id)`. Zero matches or more than one match leave the column NULL.
A row whose `rnica_assessment_id` is already non-NULL is never
overwritten. No row is ever deleted. "Latest", timestamp proximity, and
insertion order are never used to break a tie.

Forward-only. `downgrade()` is intentionally a no-op: un-merging two
already-independently-applied branches is not a meaningful schema
operation, and the backfill is additive/idempotent-safe (re-running the
same guarded UPDATE is harmless), so there is nothing destructive to
reverse.

Revision ID: e5f8a2c4b6d9
Revises: c1e2a3b4d5f6, d4e2f6a8b1c3
Create Date: 2026-10-10
"""

from typing import Sequence, Union

from alembic import op

revision: str = "e5f8a2c4b6d9"
down_revision: Union[str, Sequence[str], None] = ("c1e2a3b4d5f6", "d4e2f6a8b1c3")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Guarded backfill: only touch a body_systems_assessments row when
    # exactly one rnica_assessments row matches it on (patient_id,
    # visit_id), and only when rnica_assessment_id is currently NULL.
    op.execute(
        """
        UPDATE body_systems_assessments AS bsa
        SET rnica_assessment_id = matched.only_rnica_id
        FROM (
            SELECT
                ra.patient_id,
                ra.visit_id,
                -- COUNT(*) = 1 below guarantees exactly one element, so
                -- array_agg(...)[1] is deterministic (uuid has no MIN()).
                (array_agg(ra.id))[1] AS only_rnica_id,
                COUNT(*) AS match_count
            FROM rnica_assessments AS ra
            GROUP BY ra.patient_id, ra.visit_id
            HAVING COUNT(*) = 1
        ) AS matched
        WHERE bsa.patient_id = matched.patient_id
          AND bsa.visit_id = matched.visit_id
          AND bsa.rnica_assessment_id IS NULL
          AND matched.match_count = 1
        """
    )


def downgrade() -> None:
    # Intentional no-op -- see module docstring.
    pass
