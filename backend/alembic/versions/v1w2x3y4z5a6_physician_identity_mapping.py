"""Physician Identity Mapping: User-to-Physician linkage (identity
VERIFICATION model, not a visibility model by itself). Fail-closed —
provider-role accounts without an ACTIVE verified linkage get zero
patient/order visibility and zero signing capability (additive only).

Revision ID: v1w2x3y4z5a6
Revises: u0v1w2x3y4z5
Create Date: 2026-08-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "v1w2x3y4z5a6"
down_revision: Union[str, Sequence[str], None] = "u0v1w2x3y4z5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("physician_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("physicians.id"), nullable=True),
    )
    op.create_index("ix_users_physician_id", "users", ["physician_id"])

    op.add_column(
        "users",
        sa.Column("physician_link_status", sa.String(length=32), nullable=False, server_default="UNLINKED"),
    )
    op.create_index("ix_users_physician_link_status", "users", ["physician_link_status"])

    op.add_column("users", sa.Column("physician_linked_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("users", sa.Column("physician_linked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("physician_linkage_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("physician_linkage_reason", sa.Text(), nullable=True))

    op.add_column("users", sa.Column("physician_unlinked_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("users", sa.Column("physician_unlinked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("physician_unlink_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "physician_unlink_reason")
    op.drop_column("users", "physician_unlinked_at")
    op.drop_column("users", "physician_unlinked_by_user_id")
    op.drop_column("users", "physician_linkage_reason")
    op.drop_column("users", "physician_linkage_verified_at")
    op.drop_column("users", "physician_linked_at")
    op.drop_column("users", "physician_linked_by_user_id")
    op.drop_index("ix_users_physician_link_status", table_name="users")
    op.drop_column("users", "physician_link_status")
    op.drop_index("ix_users_physician_id", table_name="users")
    op.drop_column("users", "physician_id")
