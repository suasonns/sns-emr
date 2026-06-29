"""add form_registry anchor

Revision ID: 1e3197fad3dd
Revises: 959032ecd284
Create Date: 2026-06-26 14:54:51.639251

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '1e3197fad3dd'
down_revision: Union[str, Sequence[str], None] = '959032ecd284'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_columns = {col["name"] for col in inspector.get_columns("form_registry")}

    if "form_type" not in existing_columns:
        op.add_column("form_registry", sa.Column("form_type", sa.String(), nullable=False, server_default=""))
    if "discipline" not in existing_columns:
        op.add_column("form_registry", sa.Column("discipline", sa.String(), nullable=False, server_default=""))
    if "level_of_care" not in existing_columns:
        op.add_column("form_registry", sa.Column("level_of_care", sa.String(), nullable=True))
    if "form_family" not in existing_columns:
        op.add_column("form_registry", sa.Column("form_family", sa.String(), nullable=False, server_default=""))
    if "is_primary" not in existing_columns:
        op.add_column("form_registry", sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    if "attached_forms" not in existing_columns:
        op.add_column("form_registry", sa.Column("attached_forms", sa.JSON(), nullable=True))
    if "version" not in existing_columns:
        op.add_column("form_registry", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    if "is_active" not in existing_columns:
        op.add_column("form_registry", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    if "created_at" not in existing_columns:
        op.add_column("form_registry", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    if "updated_at" not in existing_columns:
        op.add_column("form_registry", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))

    existing_indexes = [idx["name"] for idx in inspector.get_indexes("form_registry")]
    if "ix_form_registry_resolution" not in existing_indexes:
        op.create_index(
            "ix_form_registry_resolution",
            "form_registry",
            ["form_type", "discipline", "level_of_care"],
            unique=False
        )

    existing_unique_constraints = [c["name"] for c in inspector.get_unique_constraints("form_registry")]
    if "uq_form_registry_unique_active" not in existing_unique_constraints:
        op.create_unique_constraint(
            "uq_form_registry_unique_active",
            "form_registry",
            ["form_type", "discipline", "level_of_care", "is_active"]
        )


def downgrade():
    # leave downgrade minimal to avoid unsafe automatic reversal on partially pre-existing tables
    pass