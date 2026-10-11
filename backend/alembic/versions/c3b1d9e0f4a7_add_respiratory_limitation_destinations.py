"""Add limitation_responsible_clinician_id and limitation_timing_or_contingency to system_assessments

Body Systems Phase F1 (persistence gap closure). The approved Unable-to-
Assess model (spec section 4.2, AssessmentLimitation) has six sub-fields:
scope, reason, assessedPortion, followUpRequired, responsibleClinicianId,
timingOrContingency. The first four already had backend columns
(b0d7sy5t3m5); the last two did not, and were tracked as
BACKEND_DESTINATION_MISSING in respiratoryPersistenceMapping.ts.

Adds:
  - system_assessments.limitation_responsible_clinician_id: nullable UUID
    FK to users.id, same convention already used by assessed_by /
    recorded_by / signed_by / resolved_by elsewhere in this schema.
  - system_assessments.limitation_timing_or_contingency: nullable Text,
    same convention as limitation_reason / limitation_assessed_portion.

Purely additive: two new nullable columns on an existing table. No
existing column, constraint, or enum is modified, dropped, or backfilled.
Forward-only.

Revision ID: c3b1d9e0f4a7
Revises: b0d7sy5t3m5
Create Date: 2026-10-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c3b1d9e0f4a7"
down_revision: Union[str, Sequence[str], None] = "b0d7sy5t3m5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "system_assessments",
        sa.Column(
            "limitation_responsible_clinician_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "system_assessments",
        sa.Column("limitation_timing_or_contingency", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_system_assessments_limitation_responsible_clinician_id",
        "system_assessments",
        ["limitation_responsible_clinician_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_system_assessments_limitation_responsible_clinician_id", table_name="system_assessments"
    )
    op.drop_column("system_assessments", "limitation_timing_or_contingency")
    op.drop_column("system_assessments", "limitation_responsible_clinician_id")
