"""add automatic transcription pipeline fields to visit_recordings

Revision ID: c2a3b4d5e6f7
Revises: b1f2a3c4d5e6
Create Date: 2026-08-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c2a3b4d5e6f7'
down_revision: Union[str, Sequence[str], None] = 'b1f2a3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "visit_recordings",
        sa.Column("client_recording_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_unique_constraint(
        "uq_visit_recordings_client_recording_id", "visit_recordings", ["client_recording_id"]
    )
    op.create_index(
        "ix_visit_recordings_client_recording_id", "visit_recordings", ["client_recording_id"]
    )
    op.add_column(
        "visit_recordings",
        sa.Column("transcription_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "visit_recordings",
        sa.Column("transcription_error", sa.Text(), nullable=True),
    )

    # Migrate the transcript_status vocabulary from the old placeholder
    # values (not_transcribed | pending | complete | failed) to the new
    # automatic-pipeline state machine (QUEUED | PROCESSING | COMPLETED |
    # FAILED | RETRYING). Any pre-existing rows carry over their meaning
    # 1:1 -- nothing here changes which recordings are considered done.
    op.execute("UPDATE visit_recordings SET transcript_status = 'QUEUED' WHERE transcript_status = 'not_transcribed'")
    op.execute("UPDATE visit_recordings SET transcript_status = 'PROCESSING' WHERE transcript_status = 'pending'")
    op.execute("UPDATE visit_recordings SET transcript_status = 'COMPLETED' WHERE transcript_status = 'complete'")
    op.execute("UPDATE visit_recordings SET transcript_status = 'FAILED' WHERE transcript_status = 'failed'")
    op.alter_column(
        "visit_recordings",
        "transcript_status",
        server_default=sa.text("'QUEUED'"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE visit_recordings SET transcript_status = 'not_transcribed' WHERE transcript_status = 'QUEUED'")
    op.execute("UPDATE visit_recordings SET transcript_status = 'pending' WHERE transcript_status IN ('PROCESSING', 'RETRYING')")
    op.execute("UPDATE visit_recordings SET transcript_status = 'complete' WHERE transcript_status = 'COMPLETED'")
    op.execute("UPDATE visit_recordings SET transcript_status = 'failed' WHERE transcript_status = 'FAILED'")
    op.alter_column(
        "visit_recordings",
        "transcript_status",
        server_default=sa.text("'not_transcribed'"),
    )
    op.drop_column("visit_recordings", "transcription_error")
    op.drop_column("visit_recordings", "transcription_attempts")
    op.drop_index("ix_visit_recordings_client_recording_id", table_name="visit_recordings")
    op.drop_constraint("uq_visit_recordings_client_recording_id", "visit_recordings", type_="unique")
    op.drop_column("visit_recordings", "client_recording_id")
