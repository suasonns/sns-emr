"""add form engine fields to clinical_notes

Revision ID: 44ba6a23278a
Revises: cd825533874b
Create Date: 2026-06-19 22:42:41.990533

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '44ba6a23278a'
down_revision: Union[str, Sequence[str], None] = 'cd825533874b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # ✅ Add new form engine fields

    op.add_column(
        "clinical_notes",
        sa.Column("form_key", sa.String(length=128), nullable=True),
    )

    op.add_column(
        "clinical_notes",
        sa.Column("module_payload", sa.JSON(), nullable=True),
    )

    op.add_column(
        "clinical_notes",
        sa.Column("is_primary_form", sa.Boolean(), server_default="true", nullable=False),
    )

    op.add_column(
        "clinical_notes",
        sa.Column("parent_form_id", sa.UUID(), nullable=True),
    )

    # ✅ Add FK constraint (safe)
    op.create_foreign_key(
        "fk_clinical_notes_parent_form",
        "clinical_notes",
        "clinical_notes",
        ["parent_form_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    # ⚠️ Reverse cleanly (for rollback safety)

    op.drop_constraint("fk_clinical_notes_parent_form", "clinical_notes", type_="foreignkey")

    op.drop_column("clinical_notes", "parent_form_id")
    op.drop_column("clinical_notes", "is_primary_form")
    op.drop_column("clinical_notes", "module_payload")
    op.drop_column("clinical_notes", "form_key")