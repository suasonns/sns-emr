"""add department/notes/updated_by to users (SNS Staff & Access Phase UM-2)

Revision ID: um2s1a2f3f4b5
Revises: pay3v4e5r6i7f
Create Date: 2026-09-14 16:10:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "um2s1a2f3f4b5"
down_revision = "pay3v4e5r6i7f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("department", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column(
        "users",
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_users_updated_by_users",
        "users",
        "users",
        ["updated_by"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_users_updated_by_users", "users", type_="foreignkey")
    op.drop_column("users", "updated_by")
    op.drop_column("users", "notes")
    op.drop_column("users", "department")
