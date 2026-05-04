"""add_idg_core_tables

Revision ID: 7f81611cef56
Revises: ddd7fe4c2e64
Create Date: 2026-05-02 15:39:26.415115
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ENUM

# revision identifiers, used by Alembic.
revision: str = "7f81611cef56"
down_revision: Union[str, Sequence[str], None] = "ddd7fe4c2e64"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ✅ Reference existing enums (created by ddd7fe4c2e64). DO NOT CREATE HERE.
idg_status_enum = ENUM(name="idg_status_enum", create_type=False)
idg_participation_status_enum = ENUM(name="idg_participation_status_enum", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    # ✅ Create idg_meetings only if missing
    if not insp.has_table("idg_meetings"):
        op.create_table(
            "idg_meetings",
            sa.Column("idg_id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("benefit_period_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("meeting_date", sa.Date(), nullable=False),
            sa.Column("status", idg_status_enum, nullable=False),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        )

    # ✅ Create idg_participants only if missing
    if not insp.has_table("idg_participants"):
        op.create_table(
            "idg_participants",
            sa.Column("participant_id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("idg_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("discipline", sa.String(length=50), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("participation_status", idg_participation_status_enum, nullable=False),
            sa.Column("reason_if_excused", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )

    # ✅ Create idg_notes only if missing
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

    # ✅ Create idg_md_attestations only if missing
    if not insp.has_table("idg_md_attestations"):
        op.create_table(
            "idg_md_attestations",
            sa.Column("attestation_id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("idg_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("md_user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("attestation_text", sa.Text(), nullable=False),
            sa.Column("signed_at", sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    # Drop tables only. Do NOT drop enums here (they may be shared/legacy).
    if insp.has_table("idg_md_attestations"):
        op.drop_table("idg_md_attestations")
    if insp.has_table("idg_notes"):
        op.drop_table("idg_notes")
    if insp.has_table("idg_participants"):
        op.drop_table("idg_participants")
    if insp.has_table("idg_meetings"):
        op.drop_table("idg_meetings")