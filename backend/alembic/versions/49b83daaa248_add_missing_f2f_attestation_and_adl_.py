"""add missing f2f attestation and adl count columns

Revision ID: 49b83daaa248
Revises: fc9ae4b5b5ee
Create Date: 2026-06-22 15:54:13.523467
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "49b83daaa248"
down_revision: Union[str, Sequence[str], None] = "fc9ae4b5b5ee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "f2f_encounters",
        sa.Column("adl_dependency_count", sa.Integer(), nullable=True),
    )

    op.add_column(
        "f2f_encounters",
        sa.Column("attested_at", sa.DateTime(), nullable=True),
    )

    op.add_column(
        "f2f_encounters",
        sa.Column(
            "attesting_provider_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("f2f_encounters", "attesting_provider_user_id")
    op.drop_column("f2f_encounters", "attested_at")
    op.drop_column("f2f_encounters", "adl_dependency_count")