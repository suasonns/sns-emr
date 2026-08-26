"""widen clinical_notes discipline check constraint

Revision ID: f3a7c9d2b4e1
Revises: e1b8c2ef7306
Create Date: 2026-08-26 00:00:00.000000

``ck_discipline_valid`` on ``clinical_notes`` only allowed
('RN','LVN','NP','MD','SC','MSW','LCSW','BSW') -- but the visit-creation
pipeline in app/api/visits.py (_canonicalize_discipline /
ALLOWED_VISIT_TYPES / VISIT_TYPE_ALIASES) normalizes every incoming
visit_type/discipline to one of
('RN','LVN','NP','PA','MD','SW','CHAPLAIN','AIDE','ADMINISTRATIVE') before
it is ever written to ``clinical_notes.discipline`` (SC -> CHAPLAIN,
MSW/BSW/LCSW -> SW, CHHA -> AIDE). That means the *actual* values this
column receives (PA, SW, CHAPLAIN, AIDE, ADMINISTRATIVE) were never in the
allowed list, so creating any Spiritual Counselor, MSW, or Home Health Aide
(CHHA) visit via POST /visits/ has always raised a 500 CheckViolation --
this is the root cause of "there's no way to create a CHHA visit" (and,
undiscovered until now, no reliable way to create an SC/MSW visit either).
Widen the constraint to the real normalized set, keeping the original
raw-role spellings too for backward compatibility with any existing rows.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f3a7c9d2b4e1'
down_revision: Union[str, Sequence[str], None] = 'e1b8c2ef7306'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_DISCIPLINES = "'RN','LVN','NP','MD','SC','MSW','LCSW','BSW'"
NEW_DISCIPLINES = (
    "'RN','LVN','NP','PA','MD','SC','MSW','LCSW','BSW',"
    "'SW','CHAPLAIN','AIDE','CHHA','ADMINISTRATIVE'"
)


def upgrade() -> None:
    op.drop_constraint("ck_discipline_valid", "clinical_notes", type_="check")
    op.create_check_constraint(
        "ck_discipline_valid",
        "clinical_notes",
        f"discipline IN ({NEW_DISCIPLINES})",
    )


def downgrade() -> None:
    op.drop_constraint("ck_discipline_valid", "clinical_notes", type_="check")
    op.create_check_constraint(
        "ck_discipline_valid",
        "clinical_notes",
        f"discipline IN ({OLD_DISCIPLINES})",
    )
