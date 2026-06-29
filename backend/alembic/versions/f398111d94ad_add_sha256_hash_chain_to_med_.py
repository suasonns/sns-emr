"""
add sha256 hash chain to med reconciliation audit logs

Revision ID: f398111d94ad
Revises: 0751ec491729
Create Date: 2026-06-25
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f398111d94ad"
down_revision = "0751ec491729"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "med_reconciliation_audit_logs",
        sa.Column("hash_version", sa.String(length=20), nullable=False, server_default="sha256-v1"),
    )
    op.add_column(
        "med_reconciliation_audit_logs",
        sa.Column("prev_signature_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "med_reconciliation_audit_logs",
        sa.Column("signature_hash", sa.String(length=64), nullable=True),
    )

    op.create_index(
        "ix_med_recon_audit_logs_signature_hash",
        "med_reconciliation_audit_logs",
        ["signature_hash"],
        unique=False,
    )

    # Optional cleanup of server default after creation so application owns the value
    op.alter_column(
        "med_reconciliation_audit_logs",
        "hash_version",
        server_default=None,
    )


def downgrade():
    op.drop_index("ix_med_recon_audit_logs_signature_hash", table_name="med_reconciliation_audit_logs")
    op.drop_column("med_reconciliation_audit_logs", "signature_hash")
    op.drop_column("med_reconciliation_audit_logs", "prev_signature_hash")
    op.drop_column("med_reconciliation_audit_logs", "hash_version")