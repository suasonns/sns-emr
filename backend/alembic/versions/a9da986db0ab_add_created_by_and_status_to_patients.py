"""add created_by and status to patients (drift-safe)

Revision ID: a9da986db0ab
Revises: 11fee75738cb
Create Date: 2026-05-07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = "a9da986db0ab"
down_revision = "11fee75738cb"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    insp = Inspector.from_engine(bind)
    cols = [c["name"] for c in insp.get_columns(table_name)]
    return column_name in cols


def upgrade():
    # ---- STATUS ----
    # Add status only if missing. Use server_default to avoid failing on existing rows.
    if not _has_column("patients", "status"):
        op.add_column(
            "patients",
            sa.Column(
                "status",
                sa.String(length=50),
                nullable=False,
                server_default="ACTIVE",
            ),
        )
        # Remove default after column exists, keeps schema clean going forward
        op.alter_column("patients", "status", server_default=None)

    # ---- CREATED_BY ----
    # Add created_by only if missing (nullable for legacy rows)
    if not _has_column("patients", "created_by"):
        op.add_column(
            "patients",
            sa.Column(
                "created_by",
                postgresql.UUID(as_uuid=True),
                nullable=True,
            ),
        )


def downgrade():
    # Reverse safely (drop only if exists)
    if _has_column("patients", "created_by"):
        op.drop_column("patients", "created_by")
    if _has_column("patients", "status"):
        op.drop_column("patients", "status")