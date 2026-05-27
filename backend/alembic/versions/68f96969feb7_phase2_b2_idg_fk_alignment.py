"""phase2_b2_idg_fk_alignment

Revision ID: 68f96969feb7
Revises: 159473dbc25a
Create Date: 2026-05-27 12:12:09.833204

IDG normalization + FK integrity.

Adds:
- idg_notes.idg_review_id (nullable) to anchor notes to idg_reviews

Adds guarded FKs + indexes:
- idg_md_attestations.idg_review_id -> idg_reviews.id
- idg_signatures.idg_review_id -> idg_reviews.id
- idg_notes.idg_review_id -> idg_reviews.id
- user references -> users.id (where columns exist)
- idg_reviews.patient_id -> patients.id
- idg_reviews.benefit_period_id -> benefit_periods.id
- idg_reviews.created_by -> users.id (where column exists)

Forward-only, idempotent, and safe across environments.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "68f96969feb7"
down_revision: Union[str, Sequence[str], None] = "159473dbc25a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    conn = op.get_bind()
    row = conn.execute(
        sa.text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :t
              AND column_name = :c
            """
        ),
        {"t": table_name, "c": column_name},
    ).first()
    return row is not None


def _add_column_if_missing(table_name: str, column_sql: str, column_name: str) -> None:
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = :t
                      AND column_name = :c
                ) THEN
                    EXECUTE format(
                        'ALTER TABLE public.%I ADD COLUMN %s',
                        :t,
                        :sql
                    );
                END IF;
            END
            $$;
            """
        ).bindparams(t=table_name, c=column_name, sql=column_sql)
    )


def _add_fk_if_missing(
    table_name: str,
    constraint_name: str,
    column_name: str,
    ref_table: str,
    ref_column: str,
) -> None:
    if not _column_exists(table_name, column_name):
        return

    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = :con) THEN
                    EXECUTE format(
                        'ALTER TABLE public.%I ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES public.%I (%I) ON DELETE RESTRICT',
                        :t, :con, :col, :rt, :rc
                    );
                END IF;
            END
            $$;
            """
        ).bindparams(con=constraint_name, t=table_name, col=column_name, rt=ref_table, rc=ref_column)
    )


def _create_index_if_missing(index_name: str, table_name: str, column_name: str) -> None:
    if not _column_exists(table_name, column_name):
        return

    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                      AND indexname = :ix
                ) THEN
                    EXECUTE format(
                        'CREATE INDEX %I ON public.%I (%I)',
                        :ix, :t, :c
                    );
                END IF;
            END
            $$;
            """
        ).bindparams(ix=index_name, t=table_name, c=column_name)
    )


def upgrade() -> None:
    # 1) Add idg_review_id to idg_notes (nullable; backfill handled later)
    _add_column_if_missing("idg_notes", "idg_review_id UUID NULL", "idg_review_id")
    _create_index_if_missing("ix_idg_notes_idg_review_id", "idg_notes", "idg_review_id")

    # 2) Anchor IDG tables to idg_reviews
    _add_fk_if_missing("idg_notes", "fk_idg_notes_idg_review_id", "idg_review_id", "idg_reviews", "id")
    _add_fk_if_missing(
        "idg_md_attestations",
        "fk_idg_md_attestations_idg_review_id",
        "idg_review_id",
        "idg_reviews",
        "id",
    )
    _add_fk_if_missing(
        "idg_signatures",
        "fk_idg_signatures_idg_review_id",
        "idg_review_id",
        "idg_reviews",
        "id",
    )

    _create_index_if_missing("ix_idg_md_attestations_idg_review_id", "idg_md_attestations", "idg_review_id")
    _create_index_if_missing("ix_idg_signatures_idg_review_id", "idg_signatures", "idg_review_id")

    # 3) User references (guarded)
    _add_fk_if_missing("idg_notes", "fk_idg_notes_author_user_id", "author_user_id", "users", "id")
    _add_fk_if_missing("idg_notes", "fk_idg_notes_created_by", "created_by", "users", "id")

    _add_fk_if_missing("idg_md_attestations", "fk_idg_md_attestations_md_user_id", "md_user_id", "users", "id")
    _add_fk_if_missing("idg_md_attestations", "fk_idg_md_attestations_created_by", "created_by", "users", "id")

    _add_fk_if_missing("idg_signatures", "fk_idg_signatures_user_id", "user_id", "users", "id")
    _add_fk_if_missing("idg_signatures", "fk_idg_signatures_created_by", "created_by", "users", "id")

    # 4) idg_reviews core clinical anchors (guarded)
    _add_fk_if_missing("idg_reviews", "fk_idg_reviews_patient_id", "patient_id", "patients", "id")
    _add_fk_if_missing("idg_reviews", "fk_idg_reviews_benefit_period_id", "benefit_period_id", "benefit_periods", "id")
    _add_fk_if_missing("idg_reviews", "fk_idg_reviews_created_by", "created_by", "users", "id")


def downgrade() -> None:
    # Forward-only by design (audit + clinical integrity).
    pass
