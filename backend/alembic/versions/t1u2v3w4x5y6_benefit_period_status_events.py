"""Eligibility Traceability Epic Workstream 1: BenefitPeriod audit trail.

Adds benefit_period_status_events -- an immutable, append-only event log
for every benefit-period lifecycle action (created, rolled, closed,
corrected, reopened), with a NOT NULL actor_user_id (closing the
Attribution Gap) and an optional related_certification_id groundwork
column for Workstream 6 (Certification -> BenefitPeriod linkage, deferred
pending product review).

Additive only -- no existing table is altered.

Revision ID: t1u2v3w4x5y6
Revises: 8d3911bbf250
Create Date: 2026-09-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "t1u2v3w4x5y6"
down_revision: Union[str, Sequence[str], None] = "8d3911bbf250"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "benefit_period_status_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "benefit_period_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("benefit_periods.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("previous_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("related_certification_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("certifications.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_benefit_period_status_events")),
    )
    op.create_index(
        "ix_benefit_period_status_events_tenant_id", "benefit_period_status_events", ["tenant_id"],
    )
    op.create_index(
        "ix_benefit_period_status_events_benefit_period_id", "benefit_period_status_events", ["benefit_period_id"],
    )
    op.create_index(
        "ix_benefit_period_status_events_event_type", "benefit_period_status_events", ["event_type"],
    )
    op.create_index(
        "ix_benefit_period_status_events_actor_user_id", "benefit_period_status_events", ["actor_user_id"],
    )
    op.create_index(
        "ix_benefit_period_status_events_occurred_at", "benefit_period_status_events", ["occurred_at"],
    )
    op.create_index(
        "ix_benefit_period_status_events_related_certification_id",
        "benefit_period_status_events", ["related_certification_id"],
    )
    op.create_index(
        "ix_benefit_period_status_events_created_by", "benefit_period_status_events", ["created_by"],
    )
    op.create_index(
        "ix_bp_status_events_bp_time", "benefit_period_status_events", ["benefit_period_id", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_bp_status_events_bp_time", table_name="benefit_period_status_events")
    op.drop_index("ix_benefit_period_status_events_created_by", table_name="benefit_period_status_events")
    op.drop_index("ix_benefit_period_status_events_related_certification_id", table_name="benefit_period_status_events")
    op.drop_index("ix_benefit_period_status_events_occurred_at", table_name="benefit_period_status_events")
    op.drop_index("ix_benefit_period_status_events_actor_user_id", table_name="benefit_period_status_events")
    op.drop_index("ix_benefit_period_status_events_event_type", table_name="benefit_period_status_events")
    op.drop_index("ix_benefit_period_status_events_benefit_period_id", table_name="benefit_period_status_events")
    op.drop_index("ix_benefit_period_status_events_tenant_id", table_name="benefit_period_status_events")
    op.drop_table("benefit_period_status_events")
