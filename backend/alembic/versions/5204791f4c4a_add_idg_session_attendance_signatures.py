"""add idg session attendance signatures

Revision ID: 5204791f4c4a
Revises: 428042f48054
Create Date: 2026-06-26 18:53:47.286628

Forward-only, repair-safe migration.

Purpose:
- Create idg_session if missing
- Create idg_attendance if missing
- Bring legacy idg_signatures forward safely if it already exists
- Preserve existing data / tables
- Avoid duplicate-table failures
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "5204791f4c4a"
down_revision: Union[str, Sequence[str], None] = "428042f48054"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in set(inspector.get_table_names())


def _column_exists(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {c["name"] for c in inspector.get_columns(table_name)}


def _index_exists(inspector, table_name: str, index_name: str) -> bool:
    return index_name in {ix["name"] for ix in inspector.get_indexes(table_name)}


def _unique_exists(inspector, table_name: str, uq_name: str) -> bool:
    return uq_name in {uq["name"] for uq in inspector.get_unique_constraints(table_name)}


def _check_exists(inspector, table_name: str, ck_name: str) -> bool:
    # get_check_constraints is supported by PostgreSQL inspector
    return ck_name in {ck["name"] for ck in inspector.get_check_constraints(table_name)}


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # ---------------------------------------------------------
    # idg_session
    # ---------------------------------------------------------
    if not _table_exists(inspector, "idg_session"):
        op.create_table(
            "idg_session",
            sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("plan_of_care_id", UUID, nullable=False),

            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),

            sa.Column("facilitator_user_id", UUID, nullable=True),

            # compliance / workflow state
            sa.Column("idg_status", sa.Text(), nullable=False, server_default="NOT_YET_REVIEWED"),

            # AI tool-state only (NOT compliance state)
            sa.Column("ai_assist_status", sa.Text(), nullable=False, server_default="NOT_USED"),

            # official written IDG documentation
            sa.Column("summary_note", sa.Text(), nullable=True),

            # review workflow helpers
            sa.Column("review_prompt_shown", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("ready_for_review", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("reviewed_by_user_id", UUID, nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),

            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

            sa.ForeignKeyConstraint(
                ["plan_of_care_id"],
                ["plan_of_care.id"],
                name="fk_idg_session_plan_of_care",
                ondelete="CASCADE",
            ),
            sa.CheckConstraint(
                "idg_status IN ('NOT_YET_REVIEWED','IN_PROGRESS','REVIEWED')",
                name="ck_idg_session_status",
            ),
            sa.CheckConstraint(
                "ai_assist_status IN ('NOT_USED','TRANSCRIPT_GENERATED','SUMMARY_DRAFTED','REVIEW_PENDING','FINALIZED')",
                name="ck_idg_session_ai_assist_status",
            ),
        )

    # refresh inspector after possible DDL
    inspector = sa.inspect(bind)

    if not _index_exists(inspector, "idg_session", "ix_idg_session_plan_of_care_id"):
        op.create_index("ix_idg_session_plan_of_care_id", "idg_session", ["plan_of_care_id"])

    if not _index_exists(inspector, "idg_session", "ix_idg_session_started_at"):
        op.create_index("ix_idg_session_started_at", "idg_session", ["started_at"])

    # ---------------------------------------------------------
    # idg_attendance
    # ---------------------------------------------------------
    if not _table_exists(inspector, "idg_attendance"):
        op.create_table(
            "idg_attendance",
            sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("idg_session_id", UUID, nullable=False),

            sa.Column("user_id", UUID, nullable=True),
            sa.Column("participant_name", sa.String(length=255), nullable=True),
            sa.Column("discipline", sa.String(length=64), nullable=False),

            sa.Column("attendance_mode", sa.Text(), nullable=False, server_default="IN_PERSON"),
            sa.Column("attended", sa.Boolean(), nullable=False, server_default=sa.text("true")),

            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

            sa.ForeignKeyConstraint(
                ["idg_session_id"],
                ["idg_session.id"],
                name="fk_idg_attendance_session",
                ondelete="CASCADE",
            ),
            sa.CheckConstraint(
                "attendance_mode IN ('IN_PERSON','REMOTE','PHONE','MANUAL')",
                name="ck_idg_attendance_mode",
            ),
        )

    inspector = sa.inspect(bind)

    if not _index_exists(inspector, "idg_attendance", "ix_idg_attendance_session_id"):
        op.create_index("ix_idg_attendance_session_id", "idg_attendance", ["idg_session_id"])

    if not _unique_exists(inspector, "idg_attendance", "uq_idg_attendance_session_user"):
        op.create_unique_constraint(
            "uq_idg_attendance_session_user",
            "idg_attendance",
            ["idg_session_id", "user_id", "discipline"],
        )

    # ---------------------------------------------------------
    # idg_signatures
    # ---------------------------------------------------------
    if not _table_exists(inspector, "idg_signatures"):
        op.create_table(
            "idg_signatures",
            sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("idg_session_id", UUID, nullable=False),

            sa.Column("user_id", UUID, nullable=False),
            sa.Column("discipline", sa.String(length=64), nullable=False),

            sa.Column("signature_role", sa.Text(), nullable=False, server_default="ATTENDANCE_ACK"),
            sa.Column("signed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

            sa.ForeignKeyConstraint(
                ["idg_session_id"],
                ["idg_session.id"],
                name="fk_idg_signatures_session",
                ondelete="CASCADE",
            ),
            sa.CheckConstraint(
                "signature_role IN ('ATTENDANCE_ACK','FINAL_NOTE_CONFIRM','SESSION_FINALIZER')",
                name="ck_idg_signatures_role",
            ),
        )

        op.create_index("ix_idg_signatures_session_id", "idg_signatures", ["idg_session_id"])
        op.create_unique_constraint(
            "uq_idg_signatures_session_user_role",
            "idg_signatures",
            ["idg_session_id", "user_id", "signature_role"],
        )

    else:
        # Legacy table exists. Bring it forward safely.
        if not _column_exists(inspector, "idg_signatures", "idg_session_id"):
            op.add_column(
                "idg_signatures",
                sa.Column("idg_session_id", UUID, nullable=True),
            )

        if not _column_exists(inspector, "idg_signatures", "signature_role"):
            op.add_column(
                "idg_signatures",
                sa.Column("signature_role", sa.Text(), nullable=False, server_default="ATTENDANCE_ACK"),
            )

        # refresh after adding columns
        inspector = sa.inspect(bind)

        if not _index_exists(inspector, "idg_signatures", "ix_idg_signatures_session_id"):
            op.create_index("ix_idg_signatures_session_id", "idg_signatures", ["idg_session_id"])

        if not _unique_exists(inspector, "idg_signatures", "uq_idg_signatures_session_user_role"):
            # NOTE:
            # This assumes one signature role per user per session.
            # Safe because idg_session_id is nullable initially for legacy rows.
            op.create_unique_constraint(
                "uq_idg_signatures_session_user_role",
                "idg_signatures",
                ["idg_session_id", "user_id", "signature_role"],
            )

        # Add a check constraint only if it is missing.
        # Keep legacy columns (idg_review_id, idg_meeting_id) for now.
        if not _check_exists(inspector, "idg_signatures", "ck_idg_signatures_role"):
            op.create_check_constraint(
                "ck_idg_signatures_role",
                "idg_signatures",
                "signature_role IN ('ATTENDANCE_ACK','FINAL_NOTE_CONFIRM','SESSION_FINALIZER')",
            )


def downgrade():
    # Forward-only migration by design.
    # Do not drop/rename legacy objects automatically.
    pass