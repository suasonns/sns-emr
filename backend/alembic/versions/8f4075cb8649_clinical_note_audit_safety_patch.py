"""clinical note audit safety patch

Revision ID: 8f4075cb8649
Revises: da5ca220d709
Create Date: 2026-07-17 18:14:47.585399

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8f4075cb8649'
down_revision: Union[str, Sequence[str], None] = 'da5ca220d709'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # ---------------------------------------------------------
    # 1. ADD NEW COLUMNS (SAFE / FORWARD-ONLY)
    # ---------------------------------------------------------
    op.add_column(
        "clinical_notes",
        sa.Column(
            "entered_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("NOW()"),
        ),
    )

    op.add_column(
        "clinical_notes",
        sa.Column(
            "is_late_entry",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("false"),
        ),
    )

    op.add_column(
        "clinical_notes",
        sa.Column(
            "late_entry_reason",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "clinical_notes",
        sa.Column(
            "raw_transcript",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    op.add_column(
        "clinical_notes",
        sa.Column(
            "updated_by_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    # ---------------------------------------------------------
    # 2. BACKFILL EXISTING ROWS (SAFE FOR CURRENT DATA)
    # ---------------------------------------------------------
    op.execute(
        """
        UPDATE clinical_notes
        SET entered_at = COALESCE(created_at, NOW())
        WHERE entered_at IS NULL
        """
    )

    op.execute(
        """
        UPDATE clinical_notes
        SET is_late_entry = FALSE
        WHERE is_late_entry IS NULL
        """
    )

    # ---------------------------------------------------------
    # 3. ENFORCE NOT NULL AFTER BACKFILL
    # ---------------------------------------------------------
    op.alter_column(
        "clinical_notes",
        "entered_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
        existing_server_default=sa.text("NOW()"),
    )

    op.alter_column(
        "clinical_notes",
        "is_late_entry",
        existing_type=sa.Boolean(),
        nullable=False,
        existing_server_default=sa.text("false"),
    )

    # ---------------------------------------------------------
    # 4. ADD CHECK CONSTRAINT
    # ---------------------------------------------------------
    op.create_check_constraint(
        "ck_late_entry_requires_reason",
        "clinical_notes",
        "(is_late_entry = false) OR (late_entry_reason IS NOT NULL)",
    )


def downgrade():
    # ---------------------------------------------------------
    # REVERSE ONLY WHAT THIS REVISION ADDED
    # ---------------------------------------------------------
    op.drop_constraint(
        "ck_late_entry_requires_reason",
        "clinical_notes",
        type_="check",
    )

    op.drop_column("clinical_notes", "updated_by_user_id")
    op.drop_column("clinical_notes", "raw_transcript")
    op.drop_column("clinical_notes", "late_entry_reason")
    op.drop_column("clinical_notes", "is_late_entry")
    op.drop_column("clinical_notes", "entered_at")
