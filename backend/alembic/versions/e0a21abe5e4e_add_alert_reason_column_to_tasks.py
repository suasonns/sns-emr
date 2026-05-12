from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e0a21abe5e4e"
down_revision = "96e0f404af18"
branch_labels = None
depends_on = None


def upgrade():
    """
    Add alert_reason column to tasks for compliance escalation clarity.
    """
    op.add_column(
        "tasks",
        sa.Column("alert_reason", sa.Text(), nullable=True),
    )


def downgrade():
    """
    Downgrade removes alert_reason column.
    (Kept for completeness; do not use in production rollback.)
    """
    op.drop_column("tasks", "alert_reason")