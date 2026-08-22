"""add missing facesheet payer type columns

Revision ID: b35658e9dca5
Revises: e2f558bae7ea
Create Date: 2026-08-22 03:53:57.122230

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = 'b35658e9dca5'
down_revision: Union[str, Sequence[str], None] = 'e2f558bae7ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # NOTE (2026-08-22): this duplicated p7q8r9s0t1u2 ("add patient_facesheet
    # payer source type columns for HOPE A1400"), which already adds both
    # primary_payer_type and secondary_payer_type and runs earlier in this
    # same linear history. A fresh migration replay (e.g. CI) crashed with
    # DuplicateColumn once both were present in one chain. Left as a no-op
    # (rather than deleting this revision) to preserve forward-only history;
    # the columns are already guaranteed present by p7q8r9s0t1u2 by the time
    # this revision runs.
    pass


def downgrade():
    # See upgrade(): this revision no longer owns these columns, so it must
    # not drop them out from under p7q8r9s0t1u2, whose own downgrade() is
    # responsible for removing them.
    pass