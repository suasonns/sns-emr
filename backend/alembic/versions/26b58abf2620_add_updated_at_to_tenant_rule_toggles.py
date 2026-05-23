"""add updated_at to tenant_rule_toggles

Revision ID: 26b58abf2620
Revises: b4e044173627
Create Date: 2026-05-22
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "26b58abf2620"
down_revision = "b4e044173627"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Enterprise-safe idempotent migration.

    If the column already exists (e.g., added manually under an owner role),
    do nothing. This avoids ALTER TABLE ownership requirements while allowing
    Alembic to stamp the revision.
    """
    conn = op.get_bind()
    exists = conn.execute(
        sa.text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema='public'
              AND table_name='tenant_rule_toggles'
              AND column_name='updated_at'
            """
        )
    ).scalar()

    if exists:
        return

    op.add_column(
        "tenant_rule_toggles",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    """
    Safe downgrade: only drop if the column exists.
    """
    conn = op.get_bind()
    exists = conn.execute(
        sa.text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema='public'
              AND table_name='tenant_rule_toggles'
              AND column_name='updated_at'
            """
        )
    ).scalar()

    if not exists:
        return

    # NOTE: This still requires ownership to drop; downgrade is for dev only.
    op.drop_column("tenant_rule_toggles", "updated_at")