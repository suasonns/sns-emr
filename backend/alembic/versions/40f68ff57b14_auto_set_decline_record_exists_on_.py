"""auto set decline_record_exists on bereavement_declines insert

Revision ID: 40f68ff57b14
Revises: 94dec166a2a9
Create Date: 2026-05-05 10:55:20.791146

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40f68ff57b14'
down_revision: Union[str, Sequence[str], None] = '94dec166a2a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # ------------------------------------------------------------
    # Function: set_bereavement_task_decline_flag
    # Automatically flips decline_record_exists = true
    # whenever a decline is recorded
    # ------------------------------------------------------------
    op.execute("""
    CREATE OR REPLACE FUNCTION set_bereavement_task_decline_flag()
    RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
        UPDATE bereavement_tasks
        SET decline_record_exists = true,
            updated_at = now()
        WHERE id = NEW.bereavement_task_id;

        RETURN NEW;
    END;
    $$;
    """)

    # ------------------------------------------------------------
    # Trigger: fires AFTER INSERT on bereavement_declines
    # ------------------------------------------------------------
    op.execute("""
    DROP TRIGGER IF EXISTS trg_set_bereavement_task_decline_flag
    ON bereavement_declines;
    """)

    op.execute("""
    CREATE TRIGGER trg_set_bereavement_task_decline_flag
    AFTER INSERT ON bereavement_declines
    FOR EACH ROW
    EXECUTE FUNCTION set_bereavement_task_decline_flag();
    """)


def downgrade():
    op.execute("""
    DROP TRIGGER IF EXISTS trg_set_bereavement_task_decline_flag
    ON bereavement_declines;
    """)

    op.execute("""
    DROP FUNCTION IF EXISTS set_bereavement_task_decline_flag();
    """)
