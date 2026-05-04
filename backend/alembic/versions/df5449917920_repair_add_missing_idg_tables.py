"""repair_add_missing_idg_tables

Revision ID: df5449917920
Revises: 7f81611cef56
Create Date: (keep your existing header date)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "df5449917920"
down_revision = "7f81611cef56"
branch_labels = None
depends_on = None


def upgrade():
    """
    Idempotent repair migration:
    - If IDG tables already exist, do nothing.
    - Otherwise, create missing tables.
    """
    bind = op.get_bind()
    insp = inspect(bind)

    # If the core tables exist already, this repair should be a no-op.
    if insp.has_table("idg_participants") and insp.has_table("idg_notes") and insp.has_table("idg_md_attestations"):
        return

    # NOTE: enums should already exist (created by ddd7fe4c2e64)
    # and tables should reference them via existing schema. We do NOT create enums here.

    if not insp.has_table("idg_participants"):
        op.create_table(
            "idg_participants",
            sa.Column("participant_id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("idg_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("discipline", sa.String(length=50), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("participation_status", sa.String(length=50), nullable=False),
            sa.Column("reason_if_excused", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    if not insp.has_table("idg_notes"):
        op.create_table(
            "idg_notes",
            sa.Column("idg_note_id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("idg_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("discipline", sa.String(length=50), nullable=False),
            sa.Column("author_user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("recommendations", sa.Text(), nullable=True),
            sa.Column("change_in_condition", sa.Boolean(), nullable=False),
            sa.Column("poc_change_recommended", sa.Boolean(), nullable=False),
            sa.Column("signed_at", sa.DateTime(timezone=True), nullable=False),
        )

    if not insp.has_table("idg_md_attestations"):
        op.create_table(
            "idg_md_attestations",
            sa.Column("attestation_id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("idg_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("md_user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("attestation_text", sa.Text(), nullable=False),
            sa.Column("signed_at", sa.DateTime(timezone=True), nullable=False),
        )


def downgrade():
    # Forward-safe: do not drop tables here. This is a repair migration.
    pass
