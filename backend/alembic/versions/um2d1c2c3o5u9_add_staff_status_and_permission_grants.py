"""add platform staff status + delegated permission grants

Revision ID: um2d1c2c3o5u9
Revises: um2c1c2c3o5u8
Create Date: 2026-09-21 00:00:00.000000

Two additive pieces for SNS Staff & Access (Phase UM-3):

1. `users.platform_staff_status` -- a distinct ACTIVE / SUSPENDED /
   DISABLED / REMOVED lifecycle for SNS platform staff, separate from the
   global `users.active` boolean (which stays as the single source of
   truth every login/refresh check across the ENTIRE app -- clinical,
   tenant, and platform users alike -- already relies on; it is kept in
   sync by the API layer, never replaced). Scoped in practice to
   PLATFORM_ROLES accounts; defaults every existing row to ACTIVE so no
   backfill/migration risk for clinical or tenant users.

2. `staff_permission_grants` -- delegated `staff.*` capability grants
   ("problems escalate upward, work delegates downward": a Platform Owner
   or Platform Administrator may delegate an individual capability to an
   eligible SNS staff member without changing their Platform Role). See
   app.models.staff_permission_grant and app.core.roles for the
   authoritative capability catalog/ceiling enforcement -- this table only
   stores grants, it never defines what a capability means.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'um2d1c2c3o5u9'
down_revision: Union[str, Sequence[str], None] = 'um2c1c2c3o5u8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "platform_staff_status",
            sa.String(length=32),
            nullable=False,
            server_default="ACTIVE",
        ),
    )

    op.create_table(
        "staff_permission_grants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column(
            "target_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("capability", sa.String(length=64), nullable=False),
        sa.Column(
            "granted_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("revoke_reason", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_staff_permission_grants_target_user_id",
        "staff_permission_grants",
        ["target_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_staff_permission_grants_target_user_id", table_name="staff_permission_grants")
    op.drop_table("staff_permission_grants")
    op.drop_column("users", "platform_staff_status")
