"""clinical note supervision

Revision ID: d45a0696e85b
Revises: b11a7403ad0c
Create Date: 2026-06-29 00:04:09.943938

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd45a0696e85b'
down_revision: Union[str, Sequence[str], None] = 'b11a7403ad0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ✅ ADD COLUMNS
    op.add_column(
        "clinical_notes",
        sa.Column("requires_countersign", sa.Boolean(), nullable=False, server_default=sa.false())
    )

    op.add_column(
        "clinical_notes",
        sa.Column("countersigned_by", sa.UUID(), nullable=True)
    )

    op.add_column(
        "clinical_notes",
        sa.Column("countersigned_at", sa.DateTime(timezone=True), nullable=True)
    )

    # ✅ INDEX
    op.create_index(
        "idx_clinical_note_countersign",
        "clinical_notes",
        ["countersigned_by"],
        unique=False
    )

    # ✅ CONSTRAINTS

    op.create_check_constraint(
        "ck_discipline_valid",
        "clinical_notes",
        "discipline IN ('RN','LVN','NP','MD','SC','MSW','LCSW','BSW')"
    )

    op.create_check_constraint(
        "ck_bsw_requires_flag",
        "clinical_notes",
        "(discipline != 'BSW') OR (requires_countersign = true)"
    )

    op.create_check_constraint(
        "ck_countersign_pair",
        "clinical_notes",
        "(countersigned_by IS NULL AND countersigned_at IS NULL) OR "
        "(countersigned_by IS NOT NULL AND countersigned_at IS NOT NULL)"
    )

    op.create_check_constraint(
        "ck_bsw_finalize_requires_countersign",
        "clinical_notes",
        "(discipline != 'BSW') OR (finalized_at IS NULL OR countersigned_by IS NOT NULL)"
    )

    op.create_check_constraint(
        "ck_countersign_before_finalize",
        "clinical_notes",
        "(countersigned_at IS NULL OR finalized_at IS NULL OR countersigned_at <= finalized_at)"
    )


def downgrade() -> None:

    # ✅ DROP CONSTRAINTS
    op.drop_constraint("ck_countersign_before_finalize", "clinical_notes", type_="check")
    op.drop_constraint("ck_bsw_finalize_requires_countersign", "clinical_notes", type_="check")
    op.drop_constraint("ck_countersign_pair", "clinical_notes", type_="check")
    op.drop_constraint("ck_bsw_requires_flag", "clinical_notes", type_="check")
    op.drop_constraint("ck_discipline_valid", "clinical_notes", type_="check")

    # ✅ DROP INDEX
    op.drop_index("idx_clinical_note_countersign", table_name="clinical_notes")

    # ✅ DROP COLUMNS
    op.drop_column("clinical_notes", "countersigned_at")
    op.drop_column("clinical_notes", "countersigned_by")
    op.drop_column("clinical_notes", "requires_countersign")