"""add updated_at to plan_of_care_versions

Revision ID: 3c460d203249
Revises: da48a5d6ac7b
Create Date: 2026-07-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3c460d203249'
down_revision: Union[str, Sequence[str], None] = 'da48a5d6ac7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "plan_of_care_versions",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_column("plan_of_care_versions", "updated_at")