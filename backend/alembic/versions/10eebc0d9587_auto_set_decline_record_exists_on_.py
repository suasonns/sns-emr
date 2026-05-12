"""auto set decline_record_exists on bereavement_declines insert

Revision ID: 10eebc0d9587
Revises: 40f68ff57b14
Create Date: 2026-05-05 10:59:13.182393

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '10eebc0d9587'
down_revision: Union[str, Sequence[str], None] = '40f68ff57b14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
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