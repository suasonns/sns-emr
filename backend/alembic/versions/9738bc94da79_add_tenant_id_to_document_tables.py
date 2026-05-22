"""add_tenant_id_to_document_tables

Revision ID: 9738bc94da79
Revises: 62cad5066584
Create Date: 2026-05-21 13:16:16.561379
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "9738bc94da79"
down_revision: Union[str, Sequence[str], None] = "62cad5066584"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns(table, schema="public")]
    return column in cols


def upgrade() -> None:
    # 1) Add tenant_id columns only if they don't already exist
    if not _has_column("document_notifications", "tenant_id"):
        op.add_column(
            "document_notifications",
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
            schema="public",
        )

    if not _has_column("document_idg_resolution", "tenant_id"):
        op.add_column(
            "document_idg_resolution",
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
            schema="public",
        )

    # 2) Ensure tenant_id is nullable during backfill (safe even if already nullable)
    op.alter_column("document_notifications", "tenant_id", nullable=True, schema="public")
    op.alter_column("document_idg_resolution", "tenant_id", nullable=True, schema="public")

    # 3) Backfill tenant_id from document_records (authoritative)
    op.execute(
        """
        UPDATE public.document_notifications dn
        SET tenant_id = dr.tenant_id
        FROM public.document_records dr
        WHERE dn.document_id = dr.id
          AND dn.tenant_id IS NULL
        """
    )

    op.execute(
        """
        UPDATE public.document_idg_resolution r
        SET tenant_id = dr.tenant_id
        FROM public.document_records dr
        WHERE r.document_id = dr.id
          AND r.tenant_id IS NULL
        """
    )

    # 4) Enforce NOT NULL after backfill
    op.alter_column("document_notifications", "tenant_id", nullable=False, schema="public")
    op.alter_column("document_idg_resolution", "tenant_id", nullable=False, schema="public")

    # 5) Add FK constraints if missing (Postgres-safe DO blocks)
    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'fk_document_notifications_tenant'
          ) THEN
            ALTER TABLE public.document_notifications
              ADD CONSTRAINT fk_document_notifications_tenant
              FOREIGN KEY (tenant_id) REFERENCES public.tenants(id)
              ON DELETE CASCADE;
          END IF;
        END $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'fk_document_idg_resolution_tenant'
          ) THEN
            ALTER TABLE public.document_idg_resolution
              ADD CONSTRAINT fk_document_idg_resolution_tenant
              FOREIGN KEY (tenant_id) REFERENCES public.tenants(id)
              ON DELETE CASCADE;
          END IF;
        END $$;
        """
    )

    # 6) Add indexes if missing
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_document_notifications_tenant_id ON public.document_notifications(tenant_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_document_idg_resolution_tenant_id ON public.document_idg_resolution(tenant_id);"
    )

    # 7) Prevent cross-tenant collisions for same document resolution
    # Use a unique index because it's naturally IF NOT EXISTS-friendly in Postgres.
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_document_idg_resolution_tenant_document "
        "ON public.document_idg_resolution(tenant_id, document_id);"
    )


def downgrade() -> None:
    # Conservative rollback (dev-only). Safe drops.
    op.execute("DROP INDEX IF EXISTS ux_document_idg_resolution_tenant_document;")
    op.execute("DROP INDEX IF EXISTS ix_document_idg_resolution_tenant_id;")
    op.execute("DROP INDEX IF EXISTS ix_document_notifications_tenant_id;")

    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_document_idg_resolution_tenant') THEN
            ALTER TABLE public.document_idg_resolution DROP CONSTRAINT fk_document_idg_resolution_tenant;
          END IF;
          IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_document_notifications_tenant') THEN
            ALTER TABLE public.document_notifications DROP CONSTRAINT fk_document_notifications_tenant;
          END IF;
        END $$;
        """
    )

    # Drop columns only if they exist
    if _has_column("document_idg_resolution", "tenant_id"):
        op.drop_column("document_idg_resolution", "tenant_id", schema="public")
    if _has_column("document_notifications", "tenant_id"):
        op.drop_column("document_notifications", "tenant_id", schema="public")
