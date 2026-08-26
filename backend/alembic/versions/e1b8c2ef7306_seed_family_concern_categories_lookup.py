"""seed family_concern_categories lookup

Revision ID: e1b8c2ef7306
Revises: 9a4d3c8b1e5f
Create Date: 2026-08-25 17:24:45.361335

The ``family_concern_categories`` lookup table has existed since the
consolidated baseline migration but was never seeded with rows. Every
category key referenced by
``app.services.hospitalization_prevention_service.CATEGORY_LABELS``
(the only place these keys are produced) has no matching row in the
table, so any insert into ``family_concern_clusters``/`family_concern_items``
using ``primary_category``/``concern_category`` fails its foreign key
constraint. This was discovered because
``create_or_update_family_concern_from_source`` -- which is called from
the communications-log create endpoint -- always failed with
``ForeignKeyViolation`` for ``UNCLASSIFIED_OBSERVED_PATTERN``. Seed the
full label set so the hospitalization-prevention harvest pipeline can
actually persist a concern/cluster.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1b8c2ef7306'
down_revision: Union[str, Sequence[str], None] = '9a4d3c8b1e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Keep in sync with CATEGORY_LABELS in
# app/services/hospitalization_prevention_service.py
CATEGORY_LABELS = {
    "HOSPITALIZATION_REQUEST": "Hospitalization Request",
    "ER_911_DISCUSSION": "ER / 911 Discussion",
    "COMORBIDITY_FOCUS_SHIFT": "Comorbidity Focus Shift",
    "TREATABLE_CONDITION_FOCUS": "Treatable Condition Focus",
    "POOR_INTAKE_WITH_FAMILY_CONCERN": "Poor Intake With Family Concern",
    "BLOOD_SUGAR_CONCERN": "Blood Sugar Concern",
    "HYDRATION_OR_NUTRITION_REQUEST": "Hydration / Nutrition Request",
    "MEDICATION_UNDERSTANDING_GAP": "Medication Understanding Gap",
    "DISEASE_PROCESS_UNDERSTANDING_GAP": "Disease Process Understanding Gap",
    "AGGRESSIVE_TREATMENT_REQUEST": "Aggressive Treatment Request",
    "CAREGIVER_UNABLE_TO_MANAGE": "Caregiver Unable To Manage",
    "BEHAVIORAL_ESCALATION": "Behavioral Escalation",
    "RECURRING_COMMON_CONCERN": "Recurring Common Concern",
    "UNCLASSIFIED_OBSERVED_PATTERN": "Unclassified Observed Pattern",
}


family_concern_categories = sa.table(
    "family_concern_categories",
    sa.column("category_key", sa.String),
    sa.column("display_name", sa.String),
    sa.column("active", sa.Boolean),
)


def upgrade() -> None:
    """Upgrade schema."""
    op.bulk_insert(
        family_concern_categories,
        [
            {"category_key": key, "display_name": label, "active": True}
            for key, label in CATEGORY_LABELS.items()
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    keys = tuple(CATEGORY_LABELS.keys())
    op.execute(
        sa.text(
            "DELETE FROM family_concern_categories WHERE category_key IN :keys"
        ).bindparams(sa.bindparam("keys", expanding=True)),
        {"keys": keys},
    )

