"""add task completion evidence fields (repair-safe + enum-safe)

Revision ID: e8b243e6832b
Revises: 25aebf89a1ae
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "e8b243e6832b"
down_revision: Union[str, Sequence[str], None] = "25aebf89a1ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # ---------- add columns if missing ----------
    def col_exists(col_name: str) -> bool:
        return bind.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema='public'
                      AND table_name='tasks'
                      AND column_name=:col
                );
            """),
            {"col": col_name},
        ).scalar()

    if not col_exists("completed_at"):
        op.add_column("tasks", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))

    if not col_exists("completion_reference_type"):
        op.add_column("tasks", sa.Column("completion_reference_type", sa.String(length=20), nullable=True))

    if not col_exists("completion_reference_id"):
        op.add_column("tasks", sa.Column("completion_reference_id", sa.String(length=64), nullable=True))

    # ---------- enum-safe handling ----------
    # Detect whether completion_reference_type is an ENUM (USER-DEFINED)
    row = bind.execute(
        text("""
            SELECT data_type, udt_name
            FROM information_schema.columns
            WHERE table_schema='public'
              AND table_name='tasks'
              AND column_name='completion_reference_type'
            LIMIT 1;
        """)
    ).mappings().first()

    data_type = (row["data_type"] if row else None)
    udt_name = (row["udt_name"] if row else None)

    # If it's an enum, ensure required labels exist (VISIT/NOTE/DOCUMENT)
    if data_type == "USER-DEFINED" and udt_name:
        enum_type = udt_name

        def enum_label_exists(label: str) -> bool:
            return bind.execute(
                text("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_enum e
                        JOIN pg_type t ON t.oid = e.enumtypid
                        WHERE t.typname = :typ
                          AND e.enumlabel = :lbl
                    );
                """),
                {"typ": enum_type, "lbl": label},
            ).scalar()

        # Add missing labels safely (forward-only)
        for lbl in ("VISIT", "NOTE", "DOCUMENT"):
            if not enum_label_exists(lbl):
                # No IF NOT EXISTS needed because we checked first
                op.execute(sa.text(f"ALTER TYPE {enum_type} ADD VALUE '{lbl}'"))

        # IMPORTANT: Do NOT add a redundant CHECK constraint when enum exists.
        # Enum already restricts values, and some environments may have extra enum labels.
        return

    # ---------- if NOT enum: add check constraint (repair-safe) ----------
    ck_exists = bind.execute(
        text("""
            SELECT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname='ck_tasks_completion_reference_type'
            );
        """)
    ).scalar()

    if not ck_exists:
        op.create_check_constraint(
            "ck_tasks_completion_reference_type",
            "tasks",
            "completion_reference_type IS NULL "
            "OR completion_reference_type IN ('VISIT','NOTE','DOCUMENT')",
        )


def downgrade() -> None:
    # Conservative downgrade: do not remove clinical/audit data automatically.
    pass