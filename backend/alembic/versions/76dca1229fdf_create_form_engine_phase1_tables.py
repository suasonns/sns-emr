"""create form engine phase1 tables

Revision ID: 76dca1229fdf
Revises: 0302a7da9571
Create Date: 2026-06-23 19:54:53.519739

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '76dca1229fdf'
down_revision: Union[str, Sequence[str], None] = '0302a7da9571'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "form_modules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("module_key", sa.String(length=128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_form_modules")),
        sa.UniqueConstraint("module_key", name=op.f("uq_form_modules_module_key")),
    )
    op.create_index(
        op.f("ix_form_modules_module_key"),
        "form_modules",
        ["module_key"],
        unique=False,
    )

    op.create_table(
        "form_registry",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("form_type", sa.String(length=64), nullable=False),
        sa.Column("form_family", sa.String(length=64), nullable=False),
        sa.Column("discipline", sa.String(length=32), nullable=False),
        sa.Column("level_of_care", sa.String(length=32), nullable=True),
        sa.Column("form_key", sa.String(length=128), nullable=False),
        sa.Column(
            "is_primary",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_form_registry")),
        sa.UniqueConstraint("form_key", name=op.f("uq_form_registry_form_key")),
    )
    op.create_index(
        op.f("ix_form_registry_discipline"),
        "form_registry",
        ["discipline"],
        unique=False,
    )
    op.create_index(
        op.f("ix_form_registry_form_family"),
        "form_registry",
        ["form_family"],
        unique=False,
    )
    op.create_index(
        op.f("ix_form_registry_form_key"),
        "form_registry",
        ["form_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_form_registry_form_type"),
        "form_registry",
        ["form_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_form_registry_level_of_care"),
        "form_registry",
        ["level_of_care"],
        unique=False,
    )
    op.create_index(
        "ix_form_registry_resolution",
        "form_registry",
        ["discipline", "form_type", "level_of_care"],
        unique=False,
    )

    op.create_table(
        "form_package_modules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("form_registry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("module_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["form_registry_id"],
            ["form_registry.id"],
            name=op.f("fk_form_package_modules_form_registry_id_form_registry"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["module_id"],
            ["form_modules.id"],
            name=op.f("fk_form_package_modules_module_id_form_modules"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_form_package_modules")),
        sa.UniqueConstraint(
            "form_registry_id",
            "module_id",
            name="uq_form_package_modules_registry_module",
        ),
    )
    op.create_index(
        op.f("ix_form_package_modules_form_registry_id"),
        "form_package_modules",
        ["form_registry_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_form_package_modules_module_id"),
        "form_package_modules",
        ["module_id"],
        unique=False,
    )

    op.create_table(
        "forms",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("visit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("form_registry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "is_primary",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "content",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["form_registry_id"],
            ["form_registry.id"],
            name=op.f("fk_forms_form_registry_id_form_registry"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["visit_id"],
            ["visits.id"],
            name=op.f("fk_forms_visit_id_visits"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_forms")),
    )
    op.create_index(
        op.f("ix_forms_form_registry_id"),
        "forms",
        ["form_registry_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_forms_visit_id"),
        "forms",
        ["visit_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_forms_visit_id"), table_name="forms")
    op.drop_index(op.f("ix_forms_form_registry_id"), table_name="forms")
    op.drop_table("forms")

    op.drop_index(
        op.f("ix_form_package_modules_module_id"),
        table_name="form_package_modules",
    )
    op.drop_index(
        op.f("ix_form_package_modules_form_registry_id"),
        table_name="form_package_modules",
    )
    op.drop_table("form_package_modules")

    op.drop_index("ix_form_registry_resolution", table_name="form_registry")
    op.drop_index(op.f("ix_form_registry_level_of_care"), table_name="form_registry")
    op.drop_index(op.f("ix_form_registry_form_type"), table_name="form_registry")
    op.drop_index(op.f("ix_form_registry_form_key"), table_name="form_registry")
    op.drop_index(op.f("ix_form_registry_form_family"), table_name="form_registry")
    op.drop_index(op.f("ix_form_registry_discipline"), table_name="form_registry")
    op.drop_table("form_registry")

    op.drop_index(op.f("ix_form_modules_module_key"), table_name="form_modules")
    op.drop_table("form_modules")
