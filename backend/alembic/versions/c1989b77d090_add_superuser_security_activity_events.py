"""add superuser security activity events

Revision ID: c1989b77d090
Revises: 5a0226f4b90e
Create Date: 2026-05-06 19:09:51.988581

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c1989b77d090'
down_revision: Union[str, Sequence[str], None] = '5a0226f4b90e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "security_activity_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("role", sa.Text(), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),  # e.g., BULK_EXPORT_ATTEMPT, BULK_EXPORT_ALLOWED, REAUTH_ISSUED, REAUTH_USED
        sa.Column("scope", sa.Text(), nullable=True),        # e.g., SURVEY_EXPORT_BUNDLE, BULK_PRINT
        sa.Column("patient_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("document_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("result", sa.Text(), nullable=False),      # ALLOWED / BLOCKED / INFO
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_security_activity_events_user_time", "security_activity_events", ["user_id", "event_at"])

def downgrade():
    # forward-only; leave table
    pass
