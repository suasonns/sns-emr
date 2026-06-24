"""add sla and escalation fields to tasks

Revision ID: 28394d291963
Revises: a17db9b53221
Create Date: 2026-06-17 18:10:03.312673
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


# ✅ Alembic identifiers
revision: str = "28394d291963"
down_revision: Union[str, Sequence[str], None] = "a17db9b53221"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add SLA + escalation tracking fields to tasks table.
    """

    # ✅ SLA tracking
    op.execute("""
        ALTER TABLE tasks
        ADD COLUMN IF NOT EXISTS sla_start_at TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS sla_due_at TIMESTAMPTZ;
    """)

    # ✅ Escalation tracking
    op.execute("""
        ALTER TABLE tasks
        ADD COLUMN IF NOT EXISTS escalation_level INT DEFAULT 0,
        ADD COLUMN IF NOT EXISTS escalated_at TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS escalation_reason TEXT;
    """)

    # ✅ Overdue flag
    op.execute("""
        ALTER TABLE tasks
        ADD COLUMN IF NOT EXISTS is_overdue BOOLEAN DEFAULT FALSE;
    """)


def downgrade() -> None:
    """
    Safe rollback (remove escalation fields).
    """

    op.execute("""
        ALTER TABLE tasks
        DROP COLUMN IF EXISTS sla_start_at,
        DROP COLUMN IF EXISTS sla_due_at,
        DROP COLUMN IF EXISTS escalation_level,
        DROP COLUMN IF EXISTS escalated_at,
        DROP COLUMN IF EXISTS escalation_reason,
        DROP COLUMN IF EXISTS is_overdue;
    """)