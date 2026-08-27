"""add missing facesheet hospice-snapshot and benefit-period columns

The ORM model (app/models/patient_facesheet.py) has always declared several
columns on patient_facesheet that no prior migration ever created - they
only existed in the hand-built development database (same class of gap as
b1d4c7a90e11's view): pps_score, kps_score, fast_stage, code_status,
cti_status, noe_status, primary_rn_name, social_worker_name,
benefit_period_number, benefit_period_start, benefit_period_end,
election_date, and face_to_face_due_date.

This was invisible locally because `alembic check` was run against that
already hand-edited dev DB. A fresh migration replay from base (as CI does)
first fails as soon as e2a7b8c9d0f1 tries to read
patient_facesheet.code_status during its backfill; once that is fixed,
`alembic check` against the freshly-migrated DB (not the hand-built one)
surfaces the remaining five columns as still missing.

Inserted here (between d1fdad4c35bf and e2a7b8c9d0f1) so the columns exist
before anything downstream reads them. Uses IF NOT EXISTS so it is a no-op,
additive-only, and safe to run against a hand-built dev DB that already has
some/all of these columns.

Revision ID: c4d5e6f7a8b9
Revises: d1fdad4c35bf
Create Date: 2026-08-22
"""

from typing import Sequence, Union

from alembic import op

revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = "d1fdad4c35bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STRING_COLUMNS = [
    "pps_score",
    "kps_score",
    "fast_stage",
    "code_status",
    "cti_status",
    "noe_status",
    "primary_rn_name",
    "social_worker_name",
    "benefit_period_number",
]

_DATE_COLUMNS = [
    "election_date",
    "face_to_face_due_date",
    "benefit_period_start",
    "benefit_period_end",
]


def upgrade() -> None:
    for column in _STRING_COLUMNS:
        op.execute(
            f"ALTER TABLE patient_facesheet ADD COLUMN IF NOT EXISTS {column} VARCHAR"
        )
    for column in _DATE_COLUMNS:
        op.execute(
            f"ALTER TABLE patient_facesheet ADD COLUMN IF NOT EXISTS {column} DATE"
        )


def downgrade() -> None:
    for column in [*_STRING_COLUMNS, *_DATE_COLUMNS]:
        op.execute(f"ALTER TABLE patient_facesheet DROP COLUMN IF EXISTS {column}")
