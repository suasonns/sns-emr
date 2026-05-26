"""repair: normalize idg_md_attestations link + compliance view

Revision ID: 104cd74a907d
Revises: b4a150be0d79
Create Date: 2026-05-25 17:45:20.103314
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "104cd74a907d"
down_revision: Union[str, Sequence[str], None] = "b4a150be0d79"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Ensure new normalized column exists
    op.execute(
        """
        ALTER TABLE public.idg_md_attestations
        ADD COLUMN IF NOT EXISTS idg_review_id uuid;
        """
    )

    # 2) Backfill idg_review_id from legacy idg_id (safe, idempotent)
    op.execute(
        """
        UPDATE public.idg_md_attestations
        SET idg_review_id = idg_id
        WHERE idg_review_id IS NULL
          AND idg_id IS NOT NULL;
        """
    )

    # 3) Enforce consistency if both columns exist (prevents future drift)
    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'ck_md_attestations_idg_link_consistent'
          ) THEN
            ALTER TABLE public.idg_md_attestations
            ADD CONSTRAINT ck_md_attestations_idg_link_consistent
            CHECK (
              idg_review_id IS NULL
              OR idg_id IS NULL
              OR idg_review_id = idg_id
            );
          END IF;
        END $$;
        """
    )

    # 4) Add FK from idg_review_id -> idg_reviews.id (only if missing)
    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'fk_md_attestations_idg_review'
          ) THEN
            ALTER TABLE public.idg_md_attestations
            ADD CONSTRAINT fk_md_attestations_idg_review
            FOREIGN KEY (idg_review_id) REFERENCES public.idg_reviews(id);
          END IF;
        END $$;
        """
    )

    # 5) Add index for joins/performance (only if missing)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_md_attestations_idg_review_id
        ON public.idg_md_attestations (idg_review_id);
        """
    )

    # 6) Canonical survey view (supports legacy + normalized links)
    op.execute(
        """
        CREATE OR REPLACE VIEW public.v_idg_compliance AS
        SELECT
          r.id AS idg_review_id,
          r.patient_id,
          (md.attestation_id IS NOT NULL) AS has_md_attestation,
          (COUNT(s.id) > 0)               AS has_signature
        FROM public.idg_reviews r
        LEFT JOIN public.idg_md_attestations md
          ON (md.idg_id = r.id OR md.idg_review_id = r.id)
        LEFT JOIN public.idg_signatures s
          ON s.idg_review_id = r.id
        GROUP BY r.id, r.patient_id, md.attestation_id;
        """
    )


def downgrade() -> None:
    # If you prefer true forward-only migrations, you can leave downgrade empty.
    # This downgrade is conservative: it removes only artifacts introduced here.

    op.execute("DROP VIEW IF EXISTS public.v_idg_compliance;")

    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'fk_md_attestations_idg_review'
          ) THEN
            ALTER TABLE public.idg_md_attestations
            DROP CONSTRAINT fk_md_attestations_idg_review;
          END IF;
        END $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'ck_md_attestations_idg_link_consistent'
          ) THEN
            ALTER TABLE public.idg_md_attestations
            DROP CONSTRAINT ck_md_attestations_idg_link_consistent;
          END IF;
        END $$;
        """
    )

    op.execute("DROP INDEX IF EXISTS public.ix_md_attestations_idg_review_id;")

    # Keep the column to avoid breaking code/data unexpectedly (safer).
    # If you truly want to drop it, uncomment below — but only if no code relies on it.
    # op.execute("ALTER TABLE public.idg_md_attestations DROP COLUMN IF EXISTS idg_review_id;")
