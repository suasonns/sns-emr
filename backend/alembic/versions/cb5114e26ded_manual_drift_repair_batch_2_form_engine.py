"""manual drift repair batch 2 form engine

Revision ID: cb5114e26ded
Revises: c4c85b00bad0
Create Date: 2026-06-25 18:26:38.806922

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


revision: str = "cb5114e26ded"
down_revision: Union[str, Sequence[str], None] = "c4c85b00bad0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns(table_name)}
    return column_name in columns


def upgrade() -> None:

    # =====================================================
    # form_registry
    # =====================================================
    if not _column_exists("form_registry", "updated_at"):
        op.add_column(
            "form_registry",
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not _column_exists("form_registry", "deleted_at"):
        op.add_column(
            "form_registry",
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )

    # =====================================================
    # form_modules
    # =====================================================
    if not _column_exists("form_modules", "description"):
        op.add_column(
            "form_modules",
            sa.Column("description", sa.Text(), nullable=True),
        )

    if not _column_exists("form_modules", "is_active"):
        op.add_column(
            "form_modules",
            sa.Column("is_active", sa.Boolean(), server_default=text("true"), nullable=False),
        )

    if not _column_exists("form_modules", "updated_at"):
        op.add_column(
            "form_modules",
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not _column_exists("form_modules", "deleted_at"):
        op.add_column(
            "form_modules",
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )

    # =====================================================
    # form_package_modules
    # =====================================================
    if not _column_exists("form_package_modules", "display_order"):
        op.add_column(
            "form_package_modules",
            sa.Column("display_order", sa.Integer(), nullable=True),
        )

    if not _column_exists("form_package_modules", "is_required"):
        op.add_column(
            "form_package_modules",
            sa.Column("is_required", sa.Boolean(), server_default=text("false"), nullable=False),
        )

    if not _column_exists("form_package_modules", "is_active"):
        op.add_column(
            "form_package_modules",
            sa.Column("is_active", sa.Boolean(), server_default=text("true"), nullable=False),
        )

    if not _column_exists("form_package_modules", "created_at"):
        op.add_column(
            "form_package_modules",
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    if not _column_exists("form_package_modules", "updated_at"):
        op.add_column(
            "form_package_modules",
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not _column_exists("form_package_modules", "deleted_at"):
        op.add_column(
            "form_package_modules",
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )

    # =====================================================
    # forms
    # =====================================================
    if not _column_exists("forms", "form_key"):
        op.add_column(
            "forms",
            sa.Column("form_key", sa.String(128), nullable=True),
        )

    if not _column_exists("forms", "form_family"):
        op.add_column(
            "forms",
            sa.Column("form_family", sa.String(64), nullable=True),
        )

    if not _column_exists("forms", "form_type"):
        op.add_column(
            "forms",
            sa.Column("form_type", sa.String(64), nullable=True),
        )

    if not _column_exists("forms", "status"):
        op.add_column(
            "forms",
            sa.Column("status", sa.String(32), server_default=text("'DRAFT'"), nullable=False),
        )

    if not _column_exists("forms", "finalized_at"):
        op.add_column(
            "forms",
            sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not _column_exists("forms", "finalized_by"):
        op.add_column(
            "forms",
            sa.Column("finalized_by", sa.String(64), nullable=True),
        )

    if not _column_exists("forms", "tenant_id"):
        op.add_column(
            "forms",
            sa.Column("tenant_id", sa.String(64), nullable=True),
        )


def downgrade() -> None:
    pass