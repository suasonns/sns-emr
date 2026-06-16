"""add audit fields to visits

Revision ID: 4ed222ffed27
Revises: 01ca5a8d9bf8
Create Date: 2026-06-16 00:33:41.455778

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "4ed222ffed27"
down_revision: Union[str, Sequence[str], None] = "01ca5a8d9bf8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()

    if not _column_exists(conn, "visits", "updated_by"):
        op.add_column(
            "visits",
            sa.Column(
                "updated_by",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="RESTRICT"),
                nullable=True,
            ),
        )

    if not _column_exists(conn, "visits", "deleted_at"):
        op.add_column(
            "visits",
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not _column_exists(conn, "visits", "deleted_by"):
        op.add_column(
            "visits",
            sa.Column(
                "deleted_by",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="RESTRICT"),
                nullable=True,
            ),
        )

    if not _index_exists(conn, "ix_visits_updated_by"):
        op.create_index("ix_visits_updated_by", "visits", ["updated_by"])

    if not _index_exists(conn, "ix_visits_deleted_at"):
        op.create_index("ix_visits_deleted_at", "visits", ["deleted_at"])

    if not _index_exists(conn, "ix_visits_deleted_by"):
        op.create_index("ix_visits_deleted_by", "visits", ["deleted_by"])


def downgrade():
    conn = op.get_bind()

    if _index_exists(conn, "ix_visits_deleted_by"):
        op.drop_index("ix_visits_deleted_by", table_name="visits")

    if _index_exists(conn, "ix_visits_deleted_at"):
        op.drop_index("ix_visits_deleted_at", table_name="visits")

    if _index_exists(conn, "ix_visits_updated_by"):
        op.drop_index("ix_visits_updated_by", table_name="visits")

    if _column_exists(conn, "visits", "deleted_by"):
        op.drop_column("visits", "deleted_by")

    if _column_exists(conn, "visits", "deleted_at"):
        op.drop_column("visits", "deleted_at")

    if _column_exists(conn, "visits", "updated_by"):
        op.drop_column("visits", "updated_by")


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    result = conn.execute(
        sa.text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = :table
              AND column_name = :column
            """
        ),
        {"table": table_name, "column": column_name},
    )
    return result.scalar() is not None


def _index_exists(conn, index_name: str) -> bool:
    result = conn.execute(
        sa.text(
            """
            SELECT 1
            FROM pg_indexes
            WHERE indexname = :index_name
            """
        ),
        {"index_name": index_name},
    )
    return result.scalar() is not None