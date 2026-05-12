"""add HOPE J-section symptom tables

Revision ID: 55f06e710b3e
Revises: 496930c6a3ba
Create Date: 2026-05-04 15:23:10.248426

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55f06e710b3e'
down_revision: Union[str, Sequence[str], None] = '496930c6a3ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # J2051 – Symptom assessments
    op.create_table(
        "hope_symptom_assessments",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("hope_record_id", sa.UUID(), sa.ForeignKey("hope_records.id"), nullable=False),
        sa.Column("symptom_code", sa.Text(), nullable=False),  # PAIN, DYSPNEA, ANXIETY, etc
        sa.Column("severity", sa.Integer(), nullable=True),    # CMS scale
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("assessed_by_user_id", sa.UUID(), nullable=False),
    )

    # J2052 / J2053 – Follow-up determination
    op.create_table(
        "hope_symptom_followups",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("hope_record_id", sa.UUID(), sa.ForeignKey("hope_records.id"), nullable=False),
        sa.Column("symptom_code", sa.Text(), nullable=False),
        sa.Column("followup_required", sa.Boolean(), nullable=False),
        sa.Column("followup_completed", sa.Boolean(), nullable=False),
        sa.Column("determined_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Evidence of SFV visit
    op.create_table(
        "hope_symptom_visits",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("hope_symptom_followup_id", sa.UUID(), sa.ForeignKey("hope_symptom_followups.id")),
        sa.Column("visit_id", sa.UUID(), sa.ForeignKey("visits.id")),
        sa.Column("completed_by_user_id", sa.UUID(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
    )

def downgrade():
    op.drop_table("hope_symptom_visits")
    op.drop_table("hope_symptom_followups")
    op.drop_table("hope_symptom_assessments")