"""rnica_amendments: unify decision fields, add request_source

CDPH amendment documentation requires: the request made, the disposition
(approved/denied), who decided and when, and a written justification when
denied. This migration renames the approve/deny-specific columns to a
single, unambiguous decision-of-record shape (status already tells us
whether it was an approval or denial) and adds request_source to capture
who originated the correction request.

    approved_by    -> decision_user_id
    approved_at    -> decision_timestamp
    denied_reason  -> decision_reason
    (new)          -> request_source (PATIENT | REPRESENTATIVE | STAFF |
                       INTERNAL_QA, defaults existing rows to STAFF)

Additive/renaming migration only; no other table is touched.

Revision ID: s3t4u5v6w7x8
Revises: r1s2t3u4v5w6
Create Date: 2026-08-22
"""
from alembic import op
import sqlalchemy as sa

revision = "s3t4u5v6w7x8"
down_revision = "r1s2t3u4v5w6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("rnica_amendments", "approved_by", new_column_name="decision_user_id")
    op.alter_column("rnica_amendments", "approved_at", new_column_name="decision_timestamp")
    op.alter_column("rnica_amendments", "denied_reason", new_column_name="decision_reason")

    op.add_column(
        "rnica_amendments",
        sa.Column("request_source", sa.String(16), nullable=False, server_default=sa.text("'STAFF'")),
    )


def downgrade() -> None:
    op.drop_column("rnica_amendments", "request_source")

    op.alter_column("rnica_amendments", "decision_reason", new_column_name="denied_reason")
    op.alter_column("rnica_amendments", "decision_timestamp", new_column_name="approved_at")
    op.alter_column("rnica_amendments", "decision_user_id", new_column_name="approved_by")
