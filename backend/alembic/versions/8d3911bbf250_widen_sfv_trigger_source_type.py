"""widen sfv_requirements trigger_source_type to allow RN_VISIT

Per GITHUB CORRECTION (HUV/SFV business rules): SFV is a symptom-triggered
follow-up workflow independent of HUV1/HUV2 designation. It must be
generated from ANY qualifying RN/LVN visit with moderate/severe symptom
impact, not only from INITIAL_RN_ICA or an already-HUV-designated visit.
This widens the existing check constraint to add 'RN_VISIT' as an allowed
trigger_source_type -- no new table, no new entity.

Revision ID: 8d3911bbf250
Revises: a7c93d5e1b04
Create Date: 2026-09-07
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "8d3911bbf250"
down_revision = "a7c93d5e1b04"
branch_labels = None
depends_on = None

CONSTRAINT_NAME = "ck_sfv_requirements_ck_sfv_requirements_trigger_source_type"


def upgrade() -> None:
    op.drop_constraint(op.f(CONSTRAINT_NAME), "sfv_requirements", type_="check")
    op.create_check_constraint(
        op.f(CONSTRAINT_NAME),
        "sfv_requirements",
        "trigger_source_type IN ('INITIAL_RN_ICA', 'HUV1', 'HUV2', 'RN_VISIT')",
    )


def downgrade() -> None:
    op.drop_constraint(op.f(CONSTRAINT_NAME), "sfv_requirements", type_="check")
    op.create_check_constraint(
        op.f(CONSTRAINT_NAME),
        "sfv_requirements",
        "trigger_source_type IN ('INITIAL_RN_ICA', 'HUV1', 'HUV2')",
    )
