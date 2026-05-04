"""repair drug_aliases schema

Revision ID: e7aaf711f77b
Revises: 28f85a8cd21f
Create Date: 2026-05-03 10:32:04.527888

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7aaf711f77b'
down_revision: Union[str, Sequence[str], None] = '28f85a8cd21f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)

    # 1) If table doesn't exist in THIS DB, create it correctly.
    if not insp.has_table("drug_aliases"):
        op.create_table(
            "drug_aliases",
            sa.Column("alias_text", sa.String(length=255), primary_key=True),
            sa.Column("canonical_text", sa.String(length=255), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )
        op.create_index(
            "ix_drug_aliases_canonical_text",
            "drug_aliases",
            ["canonical_text"],
        )
        return

    # 2) If table exists but columns are wrong/missing, add what we need.
    cols = {c["name"] for c in insp.get_columns("drug_aliases")}

    if "alias_text" not in cols:
        op.add_column("drug_aliases", sa.Column("alias_text", sa.String(length=255), nullable=True))

    if "canonical_text" not in cols:
        op.add_column("drug_aliases", sa.Column("canonical_text", sa.String(length=255), nullable=True))

    if "created_at" not in cols:
        op.add_column(
            "drug_aliases",
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )

    # 3) If an old single-column table exists (like your pgAdmin screenshot showed 'name'),
    # migrate it into alias_text/canonical_text so you don't lose anything.
    if "name" in cols:
        op.execute("""
            UPDATE drug_aliases
            SET alias_text = COALESCE(alias_text, lower(trim(name))),
                canonical_text = COALESCE(canonical_text, lower(trim(name)))
            WHERE name IS NOT NULL;
        """)

    # 4) Backfill NULLs (safe)
    op.execute("""
        UPDATE drug_aliases
        SET alias_text = lower(trim(alias_text)),
            canonical_text = lower(trim(canonical_text))
        WHERE alias_text IS NOT NULL OR canonical_text IS NOT NULL;
    """)

    # 5) Enforce key/index safely:
    # If alias_text isn't already the primary key, create a UNIQUE index (safer than changing PK).
    existing_indexes = {i["name"] for i in insp.get_indexes("drug_aliases")}
    if "ux_drug_aliases_alias_text" not in existing_indexes:
        op.create_index(
            "ux_drug_aliases_alias_text",
            "drug_aliases",
            ["alias_text"],
            unique=True,
        )

    if "ix_drug_aliases_canonical_text" not in existing_indexes:
        op.create_index(
            "ix_drug_aliases_canonical_text",
            "drug_aliases",
            ["canonical_text"],
        )


def downgrade():
    # Intentionally minimal downgrade: do not drop table automatically (safety).
    pass