"""add task completion audit columns (completed_by, completion_metadata)

Revision ID: a7c93d5e1b04
Revises: e0babf84fd5e
Create Date: 2026-09-15 00:00:00.000000

HOPE Update Visit (HUV1/HUV2) designation support.

Per the HOPE SFV Guide business rule: HUV1/HUV2 are not new visit types,
new assessment types, or a parallel workflow -- they are a designation on
an already-existing, already-finalized RN `Visit`, applied to the
already-existing `Task` row (task_type HUV1/HUV2) created by
hope_phase_b_engine.create_huv_tasks_from_initial_rn_ica(). The RN is
prompted ("This visit qualifies as HUV1/HUV2 -- use it?") after finalizing
a qualifying visit, and a YES answer completes that pre-existing task via
the existing app.services.task_completion_evidence.complete_task_with_evidence()
VISIT-evidence path -- no new table, no new visit type, no new assessment
type.

`complete_task_with_evidence()` already tries to set `task.completed_by`
and does not have anywhere to record *why* a task was completed (reason,
the visit's original visit_type before designation, the SOC/election date
used, and the day-window bounds validated against) for survey-defensible
audit purposes. This migration adds exactly those two columns to the
existing `tasks` table so the designation audit trail lives on the same
row task completion already writes to, instead of a separate model:

- completed_by: who completed the task (was silently dropped before --
  `hasattr(task, "completed_by")` was always False).
- completion_metadata (JSONB): free-form audit bag for completion-specific
  detail that has no dedicated column (reason, original_visit_type,
  soc_date, window_start/window_end, day_number, etc.). Nullable/optional
  for every other task type; only HUV1/HUV2 designation currently
  populates it.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a7c93d5e1b04"
down_revision = "e0babf84fd5e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column(
            "completed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "tasks",
        sa.Column(
            "completion_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("tasks", "completion_metadata")
    op.drop_column("tasks", "completed_by")
