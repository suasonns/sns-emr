"""CTI Phase 1 lifecycle expansion: tenant scoping, draft/narrative capture,
LCD evidence, expiration tracking, and immutable status-history audit trail
for certifications (additive only).

Revision ID: s8t9u0v1w2x3
Revises: r7s8t9u0v1w2
Create Date: 2026-08-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "s8t9u0v1w2x3"
down_revision: Union[str, Sequence[str], None] = "r7s8t9u0v1w2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside the same transaction that
    # uses the new value; commit ahead of the rest of this migration (same
    # pattern as b2c3d4e5f6a7_add_physician_orders.py).
    op.execute("COMMIT")
    op.execute("ALTER TYPE completionreferencetype ADD VALUE IF NOT EXISTS 'CERTIFICATION'")
    op.execute("ALTER TYPE completionreferencetype ADD VALUE IF NOT EXISTS 'RECERTIFICATION'")
    op.execute("BEGIN")

    # --- certifications: tenant scoping (was missing entirely) + Phase 1 fields ---
    op.add_column("certifications", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(
        """
        UPDATE certifications c
        SET tenant_id = p.tenant_id
        FROM patients p
        WHERE c.patient_id = p.id AND c.tenant_id IS NULL
        """
    )
    op.alter_column("certifications", "tenant_id", nullable=False)
    op.create_index("ix_certifications_tenant_id", "certifications", ["tenant_id"])

    # DRAFT | PENDING_SIGNATURE | FINALIZED | SUPERSEDED (existing rows already
    # have status="FINALIZED" — additive, no rename).
    op.add_column("certifications", sa.Column("physician_narrative", sa.Text(), nullable=True))
    op.add_column("certifications", sa.Column("supporting_evidence", sa.Text(), nullable=True))
    op.add_column("certifications", sa.Column("clinical_decline_indicators", sa.Text(), nullable=True))
    op.add_column("certifications", sa.Column("narrative_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("certifications", sa.Column("narrative_at", sa.DateTime(timezone=True), nullable=True))

    op.add_column("certifications", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))

    op.add_column("certifications", sa.Column("superseded_by_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("certifications", sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True))

    op.create_foreign_key(
        "fk_certifications_narrative_by_users", "certifications", "users", ["narrative_by"], ["id"],
    )
    op.create_foreign_key(
        "fk_certifications_superseded_by_id_certifications", "certifications", "certifications",
        ["superseded_by_id"], ["id"],
    )
    op.create_index("ix_certifications_expires_at", "certifications", ["expires_at"])
    op.create_index("ix_certifications_status", "certifications", ["status"])

    # --- immutable, append-only status/transition audit trail ---
    op.create_table(
        "certification_status_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "certification_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("certifications.id", ondelete="CASCADE"), nullable=False,
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_certification_status_events")),
    )
    op.create_index(
        "ix_certification_status_events_certification_id", "certification_status_events", ["certification_id"],
    )
    op.create_index("ix_certification_status_events_tenant_id", "certification_status_events", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_certification_status_events_tenant_id", table_name="certification_status_events")
    op.drop_index("ix_certification_status_events_certification_id", table_name="certification_status_events")
    op.drop_table("certification_status_events")

    op.drop_index("ix_certifications_status", table_name="certifications")
    op.drop_index("ix_certifications_expires_at", table_name="certifications")
    op.drop_constraint("fk_certifications_superseded_by_id_certifications", "certifications", type_="foreignkey")
    op.drop_constraint("fk_certifications_narrative_by_users", "certifications", type_="foreignkey")
    op.drop_column("certifications", "superseded_at")
    op.drop_column("certifications", "superseded_by_id")
    op.drop_column("certifications", "expires_at")
    op.drop_column("certifications", "narrative_at")
    op.drop_column("certifications", "narrative_by")
    op.drop_column("certifications", "clinical_decline_indicators")
    op.drop_column("certifications", "supporting_evidence")
    op.drop_column("certifications", "physician_narrative")
    op.drop_index("ix_certifications_tenant_id", table_name="certifications")
    op.drop_column("certifications", "tenant_id")
    # Postgres enum values cannot be dropped; CERTIFICATION/RECERTIFICATION
    # remain in completionreferencetype permanently (harmless, additive-only).
