
"""repair schema drift: add missing hospice compliance tables/columns

Revision ID: 7a1fa136d905
Revises: e216a77a1e11
Create Date: 2026-06-04 20:57:51.998135
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "7a1fa136d905"
down_revision: Union[str, Sequence[str], None] = "e216a77a1e11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "clinical_notes",
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("care_level", sa.String(), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("visit_type", sa.String(), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("visit_origin", sa.String(), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("note_category", sa.String(), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("encounter_type", sa.String(), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("discipline", sa.String(), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("encounter_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("observed_data", sa.JSON(), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("patient_reported", sa.JSON(), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("caregiver_reported", sa.JSON(), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("assessment", sa.JSON(), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("interventions", sa.JSON(), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("plan_of_care_updates", sa.JSON(), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("needs_clarification", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("red_flags", sa.JSON(), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("audit_flags", sa.JSON(), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("incident_required", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("incident_status", sa.String(), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("signed_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "clinical_notes",
        sa.Column("signed_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """
    Downgrade intentionally left minimal.

    This migration is a schema-repair migration intended to restore
    model ↔ database alignment. Rolling back these columns may result
    in data loss and is not recommended in production environments.
    """
    op.drop_column("clinical_notes", "signed_at")
    op.drop_column("clinical_notes", "signed_by")
    op.drop_column("clinical_notes", "incident_id")
    op.drop_column("clinical_notes", "incident_status")
    op.drop_column("clinical_notes", "incident_required")
    op.drop_column("clinical_notes", "audit_flags")
    op.drop_column("clinical_notes", "red_flags")
    op.drop_column("clinical_notes", "needs_clarification")
    op.drop_column("clinical_notes", "plan_of_care_updates")
    op.drop_column("clinical_notes", "interventions")
    op.drop_column("clinical_notes", "assessment")
    op.drop_column("clinical_notes", "caregiver_reported")
    op.drop_column("clinical_notes", "patient_reported")
    op.drop_column("clinical_notes", "observed_data")
    op.drop_column("clinical_notes", "encounter_date")
    op.drop_column("clinical_notes", "discipline")
    op.drop_column("clinical_notes", "encounter_type")
    op.drop_column("clinical_notes", "note_category")
    op.drop_column("clinical_notes", "visit_origin")
    op.drop_column("clinical_notes", "visit_type")
    op.drop_column("clinical_notes", "care_level")
    op.drop_column("clinical_notes", "patient_id")
