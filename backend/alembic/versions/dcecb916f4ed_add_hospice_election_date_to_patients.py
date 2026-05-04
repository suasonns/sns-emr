"""add hospice_election_date to patients

Revision ID: dcecb916f4ed
Revises: 3dec96845e87
Create Date: 2026-05-01 06:11:43.830050

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dcecb916f4ed'
down_revision: Union[str, Sequence[str], None] = '3dec96845e87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None




def upgrade():
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema='public'
              AND table_name='patients'
              AND column_name='hospice_election_date'
        ) THEN
            ALTER TABLE public.patients ADD COLUMN hospice_election_date DATE;
        END IF;
    END$$;
    """)

def downgrade():
    op.drop_column("patients", "hospice_election_date")
