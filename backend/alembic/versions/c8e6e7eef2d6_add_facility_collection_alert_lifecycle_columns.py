"""add facility collection alert lifecycle columns

Revision ID: c8e6e7eef2d6
Revises: p9r8q7s6t5u4
Create Date: 2026-09-10 00:00:00.000000

Priority 3 (Facility Collection Alerts V1) Phase 1: completes the 9-state
alert lifecycle (OPEN / ACKNOWLEDGED / IN_PROGRESS / SNOOZED / DISMISSED /
RESOLVED / AUTO_RESOLVED / SUPPRESSED / EXPIRED). Adds the four new columns
required to support ACKNOWLEDGED, SNOOZED, and DISMISSED transitions.
resolution_evidence / resolved_by / resolved_at (already present) are reused
as the generic closure record for every terminal status, so no additional
columns are needed for RESOLVED / AUTO_RESOLVED / SUPPRESSED.

Note: originally chained off e4f5a6b7c8d9, the (broken) head on main at
the time this migration was authored. hotfix/alembic-graph-reconciliation
(merged in PR #72) repointed e4f5a6b7c8d9's own down_revision to resolve
the dangling-parent break and collapsed main to a single true head,
p9r8q7s6t5u4. Rebased onto that head accordingly; no schema changes.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c8e6e7eef2d6"
down_revision = "p9r8q7s6t5u4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "facility_collection_alerts",
        sa.Column("acknowledged_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "facility_collection_alerts",
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "facility_collection_alerts",
        sa.Column("snoozed_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "facility_collection_alerts",
        sa.Column("dismissal_reason_code", sa.String(length=32), nullable=True),
    )
    op.create_foreign_key(
        "fk_facility_collection_alerts_acknowledged_by_users",
        "facility_collection_alerts",
        "users",
        ["acknowledged_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_facility_collection_alerts_acknowledged_by_users",
        "facility_collection_alerts",
        type_="foreignkey",
    )
    op.drop_column("facility_collection_alerts", "dismissal_reason_code")
    op.drop_column("facility_collection_alerts", "snoozed_until")
    op.drop_column("facility_collection_alerts", "acknowledged_at")
    op.drop_column("facility_collection_alerts", "acknowledged_by")
