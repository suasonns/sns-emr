"""add responsible_owner_id, identity_purpose, identity_scope to users

Revision ID: um2b1c2c3o5u7
Revises: um2a1c2c3o5u6
Create Date: 2026-09-14 00:00:00.000000

Phase UM-2A (final IAM direction). SNS Staff & Access separates Human
Staff from Platform Identities (Service Accounts / Automation Accounts /
API Clients). Non-human identities need a real, backend-persisted
"Responsible Owner" (an accountable SNS human staff member),
"Purpose" (why the identity exists), and, for API Clients, a "Scope"
(what it is authorized to touch) -- these must never be fabricated or
displayed as ordinary employee fields (see app/api/owner_admin.py).

`job_title` already exists on `users` (added for tenant HR profiles) and
is reused as-is for SNS staff -- no migration needed for it.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'um2b1c2c3o5u7'
down_revision: Union[str, Sequence[str], None] = 'um2a1c2c3o5u6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "responsible_owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column("users", sa.Column("identity_purpose", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("identity_scope", sa.String(length=255), nullable=True))
    op.create_index(
        "ix_users_responsible_owner_id",
        "users",
        ["responsible_owner_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_users_responsible_owner_id", table_name="users")
    op.drop_column("users", "identity_scope")
    op.drop_column("users", "identity_purpose")
    op.drop_column("users", "responsible_owner_id")
