"""add updated_at to clinical_note_versions

Revision ID: 93a8694600a9
Revises: 38140f51facd
Create Date: 2026-06-16

Purpose:
- Repair schema drift between ORM/BaseModel and DB table clinical_note_versions
- Add updated_at column required by runtime inserts
- Preserve forward-only Alembic history
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "93a8694600a9"
down_revision = "38140f51facd"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "clinical_note_versions",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )


def downgrade():
    op.drop_column("clinical_note_versions", "updated_at")
