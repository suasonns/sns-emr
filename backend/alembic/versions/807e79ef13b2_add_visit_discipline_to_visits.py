"""add visit_discipline to visits

Revision ID: 807e79ef13b2
Revises: a9da986db0ab
Create Date: 2026-05-07 21:11:52.373250
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = "807e79ef13b2"
down_revision: Union[str, Sequence[str], None] = "a9da986db0ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    insp = Inspector.from_engine(bind)
    cols = [c["name"] for c in insp.get_columns(table_name)]
    return column_name in cols


def upgrade() -> None:
    # 1) Add column (nullable first for safety)
    if not _has_column("visits", "visit_discipline"):
        op.add_column(
            "visits",
            sa.Column("visit_discipline", sa.String(length=16), nullable=True),
        )

    # 2) Backfill ONLY where old data clearly stored discipline in visit_type.
    #    (Legacy system used visit_type values like RN/LVN/NP/MD/SW/CHAPLAIN/CHHA/VOLUNTEER.)
    op.execute(
        """
        UPDATE visits
        SET visit_discipline = visit_type
        WHERE visit_discipline IS NULL
          AND visit_type IN ('RN','LVN','NP','MD','SW','CHAPLAIN','CHHA','VOLUNTEER')
        """
    )

    # 3) Enforce NOT NULL only if safe (no remaining NULLs).
    bind = op.get_bind()
    null_count = bind.execute(
        sa.text("SELECT COUNT(*) FROM visits WHERE visit_discipline IS NULL")
    ).scalar()

    if null_count == 0:
        op.alter_column("visits", "visit_discipline", nullable=False)


def downgrade() -> None:
    if _has_column("visits", "visit_discipline"):
        op.drop_column("visits", "visit_discipline")