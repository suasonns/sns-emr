"""enforce patient status transitions

Revision ID: beea7b77395c
Revises: 0c3805d7a91d
Create Date: 2026-05-26 16:26:49.395979

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'beea7b77395c'
down_revision: Union[str, Sequence[str], None] = '0c3805d7a91d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute(
        """
        CREATE OR REPLACE FUNCTION enforce_patient_status_transition()
        RETURNS trigger AS $$
        BEGIN
            -- Allow no-op
            IF NEW.status = OLD.status THEN
                RETURN NEW;
            END IF;

            -- ACTIVE may transition to DISCHARGED or DECEASED
            IF OLD.status = 'ACTIVE'
               AND NEW.status IN ('DISCHARGED', 'DECEASED') THEN
                RETURN NEW;
            END IF;

            -- All other transitions are illegal
            RAISE EXCEPTION
                'Illegal patient status transition: % → %',
                OLD.status, NEW.status;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER patients_status_transition_guard
        BEFORE UPDATE OF status ON patients
        FOR EACH ROW
        EXECUTE FUNCTION enforce_patient_status_transition();
        """
    )


def downgrade():
    op.execute(
        "DROP TRIGGER IF EXISTS patients_status_transition_guard ON patients;"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS enforce_patient_status_transition;"
    )