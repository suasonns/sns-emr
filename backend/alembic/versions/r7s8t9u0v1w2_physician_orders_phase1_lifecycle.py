"""add physician_order_status_events + phase 1 lifecycle fields

Revision ID: r7s8t9u0v1w2
Revises: a1c2d3e4f5b6
Create Date: 2026-08-21

Physician Orders Phase 1 (additive only, per owner final decision
2026-08-21): no rename of existing status literals. Preserves DRAFT,
PENDING_HOSPICE_MD_APPROVAL, APPROVED, EXECUTED, CANCELLED; adds
PENDING_CLINICAL_REVIEW, COMPLETED, EXPIRED as recognized values at the
application layer (status remains a plain String(32) column, no CHECK
constraint, consistent with the existing table).

Adds:
- physician_order_status_events: append-only, structured transition audit
  trail (who/when/why/from/to/bypass), distinct from the generic AuditLog.
- physician_orders columns needed for conditional clinical review, STAT
  bypass audit, implementation/completion/expiration tracking.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "r7s8t9u0v1w2"
down_revision: Union[str, Sequence[str], None] = "a1c2d3e4f5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "physician_order_status_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("physician_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=True),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("changed_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("changed_by_role", sa.String(length=64), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("automatic", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("clinical_review_bypassed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("clinical_review_bypass_reason", sa.Text(), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=True),
    )
    op.create_index("ix_physician_order_status_events_order_id", "physician_order_status_events", ["order_id"])
    op.create_index("ix_physician_order_status_events_tenant_id", "physician_order_status_events", ["tenant_id"])

    with op.batch_alter_table("physician_orders") as batch_op:
        # --- priority / STAT + conditional clinical-review bypass ---
        batch_op.add_column(sa.Column("priority", sa.String(length=16), nullable=False, server_default="ROUTINE"))
        batch_op.add_column(sa.Column("urgency_reason", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("clinical_review_required", sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column("clinical_reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True))
        batch_op.add_column(sa.Column("clinical_reviewed_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("clinical_review_result", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("clinical_review_bypassed", sa.Boolean(), nullable=False, server_default="false"))
        batch_op.add_column(sa.Column("clinical_review_bypass_reason", sa.Text(), nullable=True))

        # --- implementation / completion tracking (distinct from signature) ---
        batch_op.add_column(sa.Column("implemented_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True))
        batch_op.add_column(sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("completed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True))
        batch_op.add_column(sa.Column("completion_evidence", sa.Text(), nullable=True))

        # --- expiration tracking ---
        batch_op.add_column(sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("expiration_type", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index("ix_physician_orders_expires_at", "physician_orders", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_physician_orders_expires_at", table_name="physician_orders")
    with op.batch_alter_table("physician_orders") as batch_op:
        for col in [
            "priority", "urgency_reason", "clinical_review_required",
            "clinical_reviewed_by", "clinical_reviewed_at", "clinical_review_result",
            "clinical_review_bypassed", "clinical_review_bypass_reason",
            "implemented_by", "completed_at", "completed_by", "completion_evidence",
            "expires_at", "expiration_type", "expired_at",
        ]:
            batch_op.drop_column(col)
    op.drop_table("physician_order_status_events")
