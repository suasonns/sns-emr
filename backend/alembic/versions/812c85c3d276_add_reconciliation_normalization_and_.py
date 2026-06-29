"""add reconciliation normalization and comparison fields

Revision ID: 812c85c3d276
Revises: 0702c3317c6f
Create Date: 2026-06-25 15:50:45.648913
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "812c85c3d276"
down_revision: Union[str, Sequence[str], None] = "0702c3317c6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns(table_name)}
    return column_name in columns


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = {idx["name"] for idx in inspector.get_indexes(table_name)}
    return index_name in indexes


def upgrade() -> None:
    # ---------------------------------------------------------
    # NORMALIZATION FIELDS
    # ---------------------------------------------------------
    if not _column_exists("med_reconciliation_items", "dose_normalized"):
        op.add_column(
            "med_reconciliation_items",
            sa.Column("dose_normalized", sa.String(length=128), nullable=True),
        )

    if not _column_exists("med_reconciliation_items", "route_normalized"):
        op.add_column(
            "med_reconciliation_items",
            sa.Column("route_normalized", sa.String(length=64), nullable=True),
        )

    if not _column_exists("med_reconciliation_items", "frequency_normalized"):
        op.add_column(
            "med_reconciliation_items",
            sa.Column("frequency_normalized", sa.String(length=128), nullable=True),
        )

    # ---------------------------------------------------------
    # COMPARISON ENGINE FIELDS
    # ---------------------------------------------------------
    if not _column_exists("med_reconciliation_items", "comparison_status"):
        op.add_column(
            "med_reconciliation_items",
            sa.Column("comparison_status", sa.String(length=32), nullable=True),
        )

    if not _column_exists("med_reconciliation_items", "comparison_flags"):
        op.add_column(
            "med_reconciliation_items",
            sa.Column(
                "comparison_flags",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
        )

    if not _column_exists("med_reconciliation_items", "matched_medication_id"):
        op.add_column(
            "med_reconciliation_items",
            sa.Column(
                "matched_medication_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,
            ),
        )

    if not _column_exists("med_reconciliation_items", "comparison_review_reason"):
        op.add_column(
            "med_reconciliation_items",
            sa.Column("comparison_review_reason", sa.Text(), nullable=True),
        )

    # ---------------------------------------------------------
    # PERFORMANCE INDEXES
    # ---------------------------------------------------------
    if not _index_exists(
        "med_reconciliation_items",
        "ix_med_reconciliation_items_comparison_status",
    ):
        op.create_index(
            "ix_med_reconciliation_items_comparison_status",
            "med_reconciliation_items",
            ["comparison_status"],
            unique=False,
        )

    if not _index_exists(
        "med_reconciliation_items",
        "ix_med_reconciliation_items_matched_med",
    ):
        op.create_index(
            "ix_med_reconciliation_items_matched_med",
            "med_reconciliation_items",
            ["matched_medication_id"],
            unique=False,
        )


def downgrade() -> None:
    # ---------------------------------------------------------
    # DROP INDEXES FIRST (IF THEY EXIST)
    # ---------------------------------------------------------
    if _index_exists(
        "med_reconciliation_items",
        "ix_med_reconciliation_items_matched_med",
    ):
        op.drop_index(
            "ix_med_reconciliation_items_matched_med",
            table_name="med_reconciliation_items",
        )

    if _index_exists(
        "med_reconciliation_items",
        "ix_med_reconciliation_items_comparison_status",
    ):
        op.drop_index(
            "ix_med_reconciliation_items_comparison_status",
            table_name="med_reconciliation_items",
        )

    # ---------------------------------------------------------
    # DROP COLUMNS (IF THEY EXIST)
    # ---------------------------------------------------------
    if _column_exists("med_reconciliation_items", "comparison_review_reason"):
        op.drop_column("med_reconciliation_items", "comparison_review_reason")

    if _column_exists("med_reconciliation_items", "matched_medication_id"):
        op.drop_column("med_reconciliation_items", "matched_medication_id")

    if _column_exists("med_reconciliation_items", "comparison_flags"):
        op.drop_column("med_reconciliation_items", "comparison_flags")

    if _column_exists("med_reconciliation_items", "comparison_status"):
        op.drop_column("med_reconciliation_items", "comparison_status")

    if _column_exists("med_reconciliation_items", "frequency_normalized"):
        op.drop_column("med_reconciliation_items", "frequency_normalized")

    if _column_exists("med_reconciliation_items", "route_normalized"):
        op.drop_column("med_reconciliation_items", "route_normalized")

    if _column_exists("med_reconciliation_items", "dose_normalized"):
        op.drop_column("med_reconciliation_items", "dose_normalized")