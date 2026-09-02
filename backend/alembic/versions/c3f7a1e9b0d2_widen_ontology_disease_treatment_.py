"""widen ontology_disease_treatment_limitation limitation_category check constraint

Revision ID: c3f7a1e9b0d2
Revises: af1833134391
Create Date: 2026-09-01 22:40:00.000000

Additive-only change: widens the ck_ontology_disease_treatment_limitation_category
CHECK constraint to also permit the 8 approved limitation_category values used by
the Neurologic Production Source Manifest v1 import (NOT_CANDIDATE,
CONTRAINDICATED, DECLINED, NOT_TOLERATED, OUTSIDE_WINDOW, GOALS_OF_CARE,
DISCONTINUED, NOT_BENEFICIAL), while preserving every previously allowed value
(OPTIMALLY_TREATED, TREATMENT_FAILED, TREATMENT_INTOLERANT, NOT_A_CANDIDATE,
TREATMENT_DECLINED, TREATMENT_DISCONTINUED, TREATMENT_CONTRAINDICATED,
COMFORT_FOCUSED) so existing rows remain valid. No column, table, or existing
row is altered -- forward-only, additive constraint widening only.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3f7a1e9b0d2'
down_revision: Union[str, Sequence[str], None] = 'af1833134391'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_VALUES = (
    "'OPTIMALLY_TREATED', 'TREATMENT_FAILED', 'TREATMENT_INTOLERANT', 'NOT_A_CANDIDATE', "
    "'TREATMENT_DECLINED', 'TREATMENT_DISCONTINUED', 'TREATMENT_CONTRAINDICATED', 'COMFORT_FOCUSED'"
)
NEW_VALUES = (
    "'NOT_CANDIDATE', 'CONTRAINDICATED', 'DECLINED', 'NOT_TOLERATED', "
    "'OUTSIDE_WINDOW', 'GOALS_OF_CARE', 'DISCONTINUED', 'NOT_BENEFICIAL'"
)


# The table-creation migration (d635c5937cb5) named this constraint via
# op.f(...) auto-naming; the aspirational model-declared name
# ('ck_ontology_disease_treatment_limitation_category') is NOT the name
# actually installed in the database. Rather than hardcode a literal,
# resolve the real installed name at migration-run time directly from the
# Postgres catalog before dropping/recreating it. op.f(...) marks the
# resolved name as already-final so Alembic's drop/create operations use
# it literally instead of re-deriving a name from it.


def _resolve_installed_constraint_name(connection) -> str:
    row = connection.execute(
        sa.text(
            "select conname from pg_constraint "
            "where conrelid = 'ontology_disease_treatment_limitation'::regclass "
            "and contype = 'c' and pg_get_constraintdef(oid) like '%limitation_category%'"
        )
    ).fetchone()
    if row is None:
        raise RuntimeError(
            "Could not locate the existing limitation_category CHECK constraint on "
            "ontology_disease_treatment_limitation -- aborting without any change."
        )
    return row[0]


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    constraint_name = _resolve_installed_constraint_name(bind)
    op.drop_constraint(
        op.f(constraint_name),
        'ontology_disease_treatment_limitation',
        type_='check',
    )
    op.create_check_constraint(
        op.f(constraint_name),
        'ontology_disease_treatment_limitation',
        f"limitation_category IN ({OLD_VALUES}, {NEW_VALUES})",
    )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    constraint_name = _resolve_installed_constraint_name(bind)
    op.drop_constraint(
        op.f(constraint_name),
        'ontology_disease_treatment_limitation',
        type_='check',
    )
    op.create_check_constraint(
        op.f(constraint_name),
        'ontology_disease_treatment_limitation',
        f"limitation_category IN ({OLD_VALUES})",
    )
