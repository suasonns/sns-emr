"""add rnica hope workflow columns

Revision ID: 9d3f6b7c8a10
Revises: f1a2b3c4d5e6
Create Date: 2026-08-24 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "9d3f6b7c8a10"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rnica_assessments", sa.Column("hope_workflow_status", sa.String(length=32), nullable=False, server_default="OPEN"))
    op.add_column("rnica_assessments", sa.Column("hope_closed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("rnica_assessments", sa.Column("hope_closed_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("rnica_assessments", sa.Column("hope_ready_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("rnica_assessments", sa.Column("hope_ready_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("rnica_assessments", sa.Column("hope_exported_to_batch_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("rnica_assessments", sa.Column("hope_exported_to_batch_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("rnica_assessments", sa.Column("hope_export_batch_id", sa.String(length=128), nullable=True))
    op.add_column("rnica_assessments", sa.Column("hope_submission_number", sa.String(length=128), nullable=True))
    op.add_column("rnica_assessments", sa.Column("hope_already_submitted", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("rnica_assessments", sa.Column("hope_submitted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("rnica_assessments", sa.Column("hope_submitted_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("rnica_assessments", sa.Column("hope_inactivated", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("rnica_assessments", sa.Column("hope_inactivated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("rnica_assessments", sa.Column("hope_inactivated_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("rnica_assessments", sa.Column("hope_unlocked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("rnica_assessments", sa.Column("hope_unlocked_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("rnica_assessments", sa.Column("hope_unlock_reason", sa.Text(), nullable=True))

    op.execute(
        """
        UPDATE rnica_assessments
        SET
            hope_submission_number = NULLIF(BTRIM(COALESCE(form_data->'finalization'->>'hopeSubmissionNumber', '')), ''),
            hope_already_submitted = COALESCE((form_data->'finalization'->>'hopeAlreadySubmitted')::boolean, false),
            hope_submitted_at = CASE
                WHEN NULLIF(BTRIM(COALESCE(form_data->'finalization'->>'hopeSubmissionNumber', '')), '') IS NOT NULL
                    OR COALESCE((form_data->'finalization'->>'hopeAlreadySubmitted')::boolean, false)
                THEN COALESCE(locked_at, updated_at, created_at)
                ELSE NULL
            END,
            hope_workflow_status = CASE
                WHEN NULLIF(BTRIM(COALESCE(form_data->'finalization'->>'hopeSubmissionNumber', '')), '') IS NOT NULL
                    OR COALESCE((form_data->'finalization'->>'hopeAlreadySubmitted')::boolean, false)
                THEN 'SUBMITTED'
                ELSE 'OPEN'
            END
        """
    )

    op.alter_column("rnica_assessments", "hope_workflow_status", server_default=None)
    op.alter_column("rnica_assessments", "hope_already_submitted", server_default=None)
    op.alter_column("rnica_assessments", "hope_inactivated", server_default=None)


def downgrade() -> None:
    op.drop_column("rnica_assessments", "hope_unlock_reason")
    op.drop_column("rnica_assessments", "hope_unlocked_by")
    op.drop_column("rnica_assessments", "hope_unlocked_at")
    op.drop_column("rnica_assessments", "hope_inactivated_by")
    op.drop_column("rnica_assessments", "hope_inactivated_at")
    op.drop_column("rnica_assessments", "hope_inactivated")
    op.drop_column("rnica_assessments", "hope_submitted_by")
    op.drop_column("rnica_assessments", "hope_submitted_at")
    op.drop_column("rnica_assessments", "hope_already_submitted")
    op.drop_column("rnica_assessments", "hope_submission_number")
    op.drop_column("rnica_assessments", "hope_export_batch_id")
    op.drop_column("rnica_assessments", "hope_exported_to_batch_by")
    op.drop_column("rnica_assessments", "hope_exported_to_batch_at")
    op.drop_column("rnica_assessments", "hope_ready_by")
    op.drop_column("rnica_assessments", "hope_ready_at")
    op.drop_column("rnica_assessments", "hope_closed_by")
    op.drop_column("rnica_assessments", "hope_closed_at")
    op.drop_column("rnica_assessments", "hope_workflow_status")
