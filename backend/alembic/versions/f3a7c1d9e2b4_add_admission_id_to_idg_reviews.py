"""add admission_id to idg_reviews (continuity episode-scoping)

idg_reviews was created by the already-applied consolidated baseline
migration (521d501c6eea), so this is a new forward-only additive
migration rather than an edit to that baseline.

Adds a single nullable admission_id column (FK to admissions.id,
ON DELETE SET NULL) plus an index. Nullable and never backfilled: no
existing idg_reviews row can be deterministically attributed to an
admission without fabricating the linkage (patient_id/tenant_id/
benefit_period_id/review_date are all explicitly disallowed inference
sources per owner directive). Legacy rows remain historical/admission-
unassigned and are excluded from current-admission IDG review lookups
and the recommendation picker by application logic, not by a NOT NULL
constraint.

No existing column, table, constraint, or enum value is modified or
removed. No data is rewritten.

Revision ID: f3a7c1d9e2b4
Revises: 8a200af8635d
Create Date: 2026-10-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f3a7c1d9e2b4"
down_revision: Union[str, Sequence[str], None] = "8a200af8635d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "idg_reviews",
        sa.Column("admission_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_idg_reviews_admission",
        "idg_reviews",
        "admissions",
        ["admission_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_idg_reviews_admission_id", "idg_reviews", ["admission_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_idg_reviews_admission_id", table_name="idg_reviews")
    op.drop_constraint("fk_idg_reviews_admission", "idg_reviews", type_="foreignkey")
    op.drop_column("idg_reviews", "admission_id")
