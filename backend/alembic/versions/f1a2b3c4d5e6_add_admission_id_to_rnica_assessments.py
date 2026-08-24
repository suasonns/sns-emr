"""add admission_id to rnica_assessments

The RN Initial Comprehensive Assessment (RNICA) is only ever performed
once per admission episode. This column scopes each RnicaAssessment row
to the Admission it belongs to, so the backend can enforce "one initial
RNICA per admission" while still allowing a brand-new one after a
discharge + re-admission (a new Admission row).

Revision ID: f1a2b3c4d5e6
Revises: e7f8a9b0c1d2
Create Date: 2026-08-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = "e7f8a9b0c1d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "rnica_assessments",
        sa.Column("admission_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_rnica_assessments_admission_id", "rnica_assessments", ["admission_id"]
    )
    op.create_foreign_key(
        "fk_rnica_assessments_admission_id",
        "rnica_assessments",
        "admissions",
        ["admission_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_rnica_assessments_admission_id", "rnica_assessments", type_="foreignkey"
    )
    op.drop_index("ix_rnica_assessments_admission_id", table_name="rnica_assessments")
    op.drop_column("rnica_assessments", "admission_id")
