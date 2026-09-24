"""Create record_versions (generic polymorphic versioning)

Revision ID: f5ed0b859dcf
Revises: aa9e08e3848e
Create Date: 2026-09-21

Generic record-versioning table for compliance-domain records that don't
already have a dedicated version concept. Election addendum versioning
already lives on election_addendum_requests.version_number/
supersedes_request_id; Plan of Care already has plan_of_care_versions.
This table does not duplicate either.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f5ed0b859dcf"
down_revision = "aa9e08e3848e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "record_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_record_type", sa.String(length=64), nullable=False),
        sa.Column("source_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("change_reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_record_versions_tenant_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_record_versions_created_by"),
        sa.PrimaryKeyConstraint("id", name="pk_record_versions"),
        sa.UniqueConstraint(
            "source_record_type", "source_record_id", "version_number", name="uq_record_versions_source_version"
        ),
        sa.CheckConstraint("version_number > 0", name="ck_record_versions_version_positive"),
    )
    op.create_index("ix_record_versions_tenant_id", "record_versions", ["tenant_id"])
    op.create_index(
        "ix_record_versions_tenant_source",
        "record_versions",
        ["tenant_id", "source_record_type", "source_record_id"],
    )
    op.create_index("ix_record_versions_source_record_type", "record_versions", ["source_record_type"])
    op.create_index("ix_record_versions_source_record_id", "record_versions", ["source_record_id"])


def downgrade() -> None:
    op.drop_table("record_versions")
