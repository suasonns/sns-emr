"""create_idg_enums

Revision ID: ddd7fe4c2e64
Revises: b09834bb4c56
Create Date: 2026-05-02 16:16:49.060104
"""

from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ddd7fe4c2e64"
down_revision: Union[str, Sequence[str], None] = "b09834bb4c56"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create enums if missing (idempotent)
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'idg_status_enum') THEN
            CREATE TYPE idg_status_enum AS ENUM ('SCHEDULED','IN_PROGRESS','COMPLETED');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'idg_participation_status_enum') THEN
            CREATE TYPE idg_participation_status_enum AS ENUM ('PRESENT','NOT_PRESENT','EXCUSED');
        END IF;
    END $$;
    """)


def downgrade():
    op.execute("DROP TYPE IF EXISTS idg_participation_status_enum;")
    op.execute("DROP TYPE IF EXISTS idg_status_enum;")
