"""Add rnica_assessment_id to body_systems_assessments

Episode/RNICA isolation fix identified during the live RNICA mount
milestone: `body_systems_assessments` previously had no column scoping it
to the specific RN ICA episode (`rnica_assessments.id` — the same identity
`/rnica/{assessment_id}` already authorizes on in app/api/visits.py). A
patient-only "most recent non-signed" lookup cannot distinguish two RNICA
episodes for the same patient. This migration is purely additive: one new
nullable FK column + index. No existing column, constraint, or data is
modified or dropped. Forward-only.

Revision ID: c1e2a3b4d5f6
Revises: b0d7sy5t3m5
Create Date: 2026-10-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c1e2a3b4d5f6"
down_revision: Union[str, Sequence[str], None] = "b0d7sy5t3m5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "body_systems_assessments",
        sa.Column(
            "rnica_assessment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rnica_assessments.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_body_systems_assessments_rnica_assessment_id",
        "body_systems_assessments",
        ["rnica_assessment_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_body_systems_assessments_rnica_assessment_id", table_name="body_systems_assessments")
    op.drop_column("body_systems_assessments", "rnica_assessment_id")
