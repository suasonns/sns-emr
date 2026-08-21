"""F2F Phase 1 lifecycle expansion: tenant scoping, physician/NP performer
authority fields, and immutable status-history audit trail for F2F
encounters (additive only).

Revision ID: t9u0v1w2x3y4
Revises: s8t9u0v1w2x3
Create Date: 2026-08-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "t9u0v1w2x3y4"
down_revision: Union[str, Sequence[str], None] = "s8t9u0v1w2x3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside the same transaction that
    # uses the new value; commit ahead of the rest of this migration (same
    # pattern as b2c3d4e5f6a7_add_physician_orders.py / s8t9u0v1w2x3).
    op.execute("COMMIT")
    op.execute("ALTER TYPE completionreferencetype ADD VALUE IF NOT EXISTS 'F2F_ENCOUNTER'")
    op.execute("BEGIN")

    # --- f2f_encounters: tenant scoping (was missing entirely) ---
    op.add_column("f2f_encounters", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(
        """
        UPDATE f2f_encounters f
        SET tenant_id = p.tenant_id
        FROM patients p
        WHERE f.patient_id = p.id AND f.tenant_id IS NULL
        """
    )
    op.alter_column("f2f_encounters", "tenant_id", nullable=False)
    op.create_index("ix_f2f_encounters_tenant_id", "f2f_encounters", ["tenant_id"])
    op.create_index("ix_f2f_encounters_status", "f2f_encounters", ["status"])

    # --- immutable, append-only status/transition audit trail ---
    op.create_table(
        "f2f_encounter_status_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "f2f_encounter_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("f2f_encounters.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("from_status", sa.String(length=32), nullable=True),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("changed_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("changed_by_role", sa.String(length=64), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("automatic", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_f2f_encounter_status_events")),
    )
    op.create_index(
        "ix_f2f_encounter_status_events_f2f_encounter_id", "f2f_encounter_status_events", ["f2f_encounter_id"],
    )
    op.create_index("ix_f2f_encounter_status_events_tenant_id", "f2f_encounter_status_events", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_f2f_encounter_status_events_tenant_id", table_name="f2f_encounter_status_events")
    op.drop_index("ix_f2f_encounter_status_events_f2f_encounter_id", table_name="f2f_encounter_status_events")
    op.drop_table("f2f_encounter_status_events")

    op.drop_index("ix_f2f_encounters_status", table_name="f2f_encounters")
    op.drop_index("ix_f2f_encounters_tenant_id", table_name="f2f_encounters")
    op.drop_column("f2f_encounters", "tenant_id")
    # Postgres enum values cannot be dropped; F2F_ENCOUNTER remains in
    # completionreferencetype permanently (harmless, additive-only).
