"""add_visits_visit_discipline (rebuild-safe)

Revision ID: 1b65d1470563
Revises: 288d8809a335
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "1b65d1470563"
down_revision = "288d8809a335"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)

    if "visits" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("visits")}

    # ✅ SAFE COLUMN ADD
    if "visit_discipline" not in columns:
        op.add_column(
            "visits",
            sa.Column("visit_discipline", sa.String(length=32), nullable=True),
        )


def downgrade():
    # ✅ forward-only
    pass