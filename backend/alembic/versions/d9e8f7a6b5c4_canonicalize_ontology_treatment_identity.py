"""canonicalize ontology treatment identity

Revision ID: d9e8f7a6b5c4
Revises: c3f7a1e9b0d2
Create Date: 2026-09-03 12:00:00.000000

Adds canonical normalized-name identity columns to ontology treatment tables,
merges pre-existing duplicate rows created by category-sensitive identity,
remaps polymorphic references, and enforces uniqueness on
(disease_id, normalized_name).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9e8f7a6b5c4'
down_revision: Union[str, Sequence[str], None] = 'c3f7a1e9b0d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TREATMENT_TABLE = "ontology_disease_treatment"
LIMITATION_TABLE = "ontology_disease_treatment_limitation"
NORMALIZED_COLUMN = "normalized_name"
OLD_TREATMENT_UQ = "uq_ontology_disease_treatment_disease_name"
OLD_LIMITATION_UQ = "uq_ontology_disease_treatment_limitation_disease_name"
NEW_TREATMENT_UQ = "uq_ont_dis_treat_disease_norm_name"
NEW_LIMITATION_UQ = "uq_ont_dis_txlim_disease_norm_name"
TREATMENT_CONCEPT_TYPE = "TREATMENT"
LIMITATION_CONCEPT_TYPE = "TREATMENT_LIMITATION"

TREATMENT_CATEGORY_PREFERENCE = {
    ("serial casting", frozenset({"DISEASE_DIRECTED", "SUPPORTIVE"})): "DISEASE_DIRECTED",
}
LIMITATION_CATEGORY_PREFERENCE = {
    frozenset({"CONTRAINDICATED", "TREATMENT_CONTRAINDICATED"}): "CONTRAINDICATED",
    frozenset({"DECLINED", "TREATMENT_DECLINED"}): "DECLINED",
    frozenset({"DISCONTINUED", "TREATMENT_DISCONTINUED"}): "DISCONTINUED",
    frozenset({"NOT_TOLERATED", "TREATMENT_INTOLERANT"}): "NOT_TOLERATED",
    frozenset({"NOT_CANDIDATE", "NOT_A_CANDIDATE"}): "NOT_CANDIDATE",
    frozenset({"GOALS_OF_CARE", "COMFORT_FOCUSED"}): "GOALS_OF_CARE",
    frozenset({"NOT_BENEFICIAL", "NOT_A_CANDIDATE"}): "NOT_BENEFICIAL",
}


def _normalize_sql(column_name: str) -> str:
    return f"lower(regexp_replace(btrim({column_name}), '\\s+', ' ', 'g'))"


def _backfill_normalized_name(connection, table_name: str, name_column: str) -> None:
    connection.execute(
        sa.text(
            f"""
            UPDATE {table_name}
               SET {NORMALIZED_COLUMN} = {_normalize_sql(name_column)}
             WHERE {NORMALIZED_COLUMN} IS NULL
                OR {NORMALIZED_COLUMN} <> {_normalize_sql(name_column)}
            """
        )
    )


def _resolve_unique_constraint_name(connection, table_name: str, column_names: tuple[str, ...], fallback: str) -> str:
    predicates = " AND ".join(
        [f"pg_get_constraintdef(oid) LIKE '%{column_name}%'" for column_name in column_names]
    )
    row = connection.execute(
        sa.text(
            f"""
            SELECT conname
              FROM pg_constraint
             WHERE conrelid = '{table_name}'::regclass
               AND contype = 'u'
               AND {predicates}
             ORDER BY conname
             LIMIT 1
            """
        )
    ).fetchone()
    return row[0] if row is not None else fallback


def _drop_constraint_if_exists(connection, table_name: str, constraint_name: str) -> None:
    connection.execute(sa.text(f'ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS "{constraint_name}"'))


def _duplicate_groups(connection, table_name: str) -> list[dict]:
    # Neither ontology_disease_treatment nor ontology_disease_treatment_limitation
    # has a created_at/inserted_at column, so `id` (a random UUID) carries no
    # temporal information. Ordering survivor selection by `id` picks an
    # effectively RANDOM row as survivor (whichever UUID sorts lower), which is
    # non-deterministic across otherwise-identical migration runs.
    #
    # `ctid` reflects each row's physical position on disk, which for rows
    # inserted by sequential importer runs (without an intervening VACUUM FULL)
    # corresponds to insertion order. Ordering by `ctid` deterministically
    # preserves "the row created first" as the survivor, matching the intent
    # of the category-reconciliation rules below (the earliest-created row's
    # identity/provenance is preserved; later duplicate imports are merged in).
    rows = connection.execute(
        sa.text(
            f"""
            SELECT disease_id,
                   {NORMALIZED_COLUMN},
                   array_agg(id ORDER BY ctid) AS ids
              FROM {table_name}
             GROUP BY disease_id, {NORMALIZED_COLUMN}
            HAVING count(*) > 1
            """
        )
    ).mappings()
    return [dict(row) for row in rows]


def _preferred_category(concept_type: str, normalized_name: str, categories: list[str]) -> str | None:
    pair = frozenset(categories)
    if concept_type == TREATMENT_CONCEPT_TYPE:
        return TREATMENT_CATEGORY_PREFERENCE.get((normalized_name, pair))
    return LIMITATION_CATEGORY_PREFERENCE.get(pair)


def _remap_concept_references(connection, concept_type: str, loser_id, survivor_id) -> None:
    for statement in (
        sa.text(
            """
            UPDATE ontology_evidence_rule
               SET concept_id = :survivor_id
             WHERE concept_type = :concept_type AND concept_id = :loser_id
            """
        ),
        sa.text(
            """
            UPDATE ontology_concept_variant_applicability
               SET concept_id = :survivor_id
             WHERE concept_type = :concept_type AND concept_id = :loser_id
            """
        ),
        sa.text(
            """
            UPDATE ontology_relationship
               SET source_concept_id = :survivor_id
             WHERE source_concept_type = :concept_type AND source_concept_id = :loser_id
            """
        ),
        sa.text(
            """
            UPDATE ontology_relationship
               SET target_concept_id = :survivor_id
             WHERE target_concept_type = :concept_type AND target_concept_id = :loser_id
            """
        ),
    ):
        connection.execute(
            statement,
            {"concept_type": concept_type, "loser_id": loser_id, "survivor_id": survivor_id},
        )


def _dedupe_supporting_tables(connection, concept_type: str) -> None:
    connection.execute(
        sa.text(
            """
            DELETE FROM ontology_evidence_rule a
             USING ontology_evidence_rule b
             WHERE a.id > b.id
               AND a.concept_type = :concept_type
               AND b.concept_type = :concept_type
               AND a.concept_type = b.concept_type
               AND a.concept_id = b.concept_id
            """
        ),
        {"concept_type": concept_type},
    )
    connection.execute(
        sa.text(
            """
            DELETE FROM ontology_concept_variant_applicability a
             USING ontology_concept_variant_applicability b
             WHERE a.id > b.id
               AND a.concept_type = :concept_type
               AND b.concept_type = :concept_type
               AND a.concept_type = b.concept_type
               AND a.concept_id = b.concept_id
               AND a.variant_id = b.variant_id
               AND a.applicability_type = b.applicability_type
            """
        ),
        {"concept_type": concept_type},
    )
    connection.execute(
        sa.text(
            """
            DELETE FROM ontology_relationship a
             USING ontology_relationship b
             WHERE a.id > b.id
               AND (
                    (a.source_concept_type = :concept_type AND b.source_concept_type = :concept_type)
                 OR (a.target_concept_type = :concept_type AND b.target_concept_type = :concept_type)
               )
               AND a.source_concept_type = b.source_concept_type
               AND a.source_concept_id = b.source_concept_id
               AND a.relationship_type = b.relationship_type
               AND a.target_concept_type = b.target_concept_type
               AND a.target_concept_id = b.target_concept_id
            """
        ),
        {"concept_type": concept_type},
    )


def _merge_duplicate_groups(connection, table_name: str, concept_type: str) -> None:
    for group in _duplicate_groups(connection, table_name):
        ids = list(group["ids"])
        survivor_id = ids[0]
        loser_ids = ids[1:]
        category_column = "treatment_category" if concept_type == TREATMENT_CONCEPT_TYPE else "limitation_category"
        rows = [
            connection.execute(
                sa.text(
                    f"SELECT id, {NORMALIZED_COLUMN}, {category_column} AS category FROM {table_name} WHERE id = :row_id"
                ),
                {"row_id": row_id},
            ).mappings().one()
            for row_id in ids
        ]
        preferred = _preferred_category(
            concept_type,
            group[NORMALIZED_COLUMN],
            [row["category"] for row in rows],
        )
        for loser_id in loser_ids:
            _remap_concept_references(connection, concept_type, loser_id, survivor_id)
        _dedupe_supporting_tables(connection, concept_type)
        for loser_id in loser_ids:
            connection.execute(
                sa.text(f"DELETE FROM {table_name} WHERE id = :loser_id"),
                {"loser_id": loser_id},
            )
        if preferred is not None:
            connection.execute(
                sa.text(
                    f"UPDATE {table_name} SET {category_column} = :preferred WHERE id = :survivor_id"
                ),
                {"preferred": preferred, "survivor_id": survivor_id},
            )


def _assert_no_orphans(connection, concept_type: str, table_name: str) -> None:
    for query, label in (
        (
            sa.text(
                f"""
                SELECT count(*)
                  FROM ontology_evidence_rule er
                 WHERE er.concept_type = :concept_type
                   AND NOT EXISTS (
                       SELECT 1 FROM {table_name} t WHERE t.id = er.concept_id
                   )
                """
            ),
            "ontology_evidence_rule",
        ),
        (
            sa.text(
                f"""
                SELECT count(*)
                  FROM ontology_concept_variant_applicability a
                 WHERE a.concept_type = :concept_type
                   AND NOT EXISTS (
                       SELECT 1 FROM {table_name} t WHERE t.id = a.concept_id
                   )
                """
            ),
            "ontology_concept_variant_applicability",
        ),
        (
            sa.text(
                f"""
                SELECT count(*)
                  FROM ontology_relationship r
                 WHERE (
                        r.source_concept_type = :concept_type
                    AND NOT EXISTS (SELECT 1 FROM {table_name} t WHERE t.id = r.source_concept_id)
                 ) OR (
                        r.target_concept_type = :concept_type
                    AND NOT EXISTS (SELECT 1 FROM {table_name} t WHERE t.id = r.target_concept_id)
                 )
                """
            ),
            "ontology_relationship",
        ),
    ):
        count = connection.execute(query, {"concept_type": concept_type}).scalar_one()
        if count:
            raise RuntimeError(f"Orphan {concept_type} references remain in {label}: {count}")


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    op.add_column(TREATMENT_TABLE, sa.Column(NORMALIZED_COLUMN, sa.String(length=255), nullable=True))
    op.add_column(LIMITATION_TABLE, sa.Column(NORMALIZED_COLUMN, sa.String(length=255), nullable=True))
    op.create_index(op.f(f"ix_{TREATMENT_TABLE}_{NORMALIZED_COLUMN}"), TREATMENT_TABLE, [NORMALIZED_COLUMN], unique=False)
    op.create_index(op.f(f"ix_{LIMITATION_TABLE}_{NORMALIZED_COLUMN}"), LIMITATION_TABLE, [NORMALIZED_COLUMN], unique=False)

    _backfill_normalized_name(bind, TREATMENT_TABLE, "treatment_name")
    _backfill_normalized_name(bind, LIMITATION_TABLE, "limitation_name")

    _merge_duplicate_groups(bind, TREATMENT_TABLE, TREATMENT_CONCEPT_TYPE)
    _merge_duplicate_groups(bind, LIMITATION_TABLE, LIMITATION_CONCEPT_TYPE)

    _drop_constraint_if_exists(
        bind,
        TREATMENT_TABLE,
        _resolve_unique_constraint_name(bind, TREATMENT_TABLE, ("disease_id", "treatment_name", "treatment_category"), OLD_TREATMENT_UQ),
    )
    _drop_constraint_if_exists(
        bind,
        LIMITATION_TABLE,
        _resolve_unique_constraint_name(bind, LIMITATION_TABLE, ("disease_id", "limitation_name", "limitation_category"), OLD_LIMITATION_UQ),
    )

    op.alter_column(TREATMENT_TABLE, NORMALIZED_COLUMN, existing_type=sa.String(length=255), nullable=False)
    op.alter_column(LIMITATION_TABLE, NORMALIZED_COLUMN, existing_type=sa.String(length=255), nullable=False)

    op.create_unique_constraint(NEW_TREATMENT_UQ, TREATMENT_TABLE, ["disease_id", NORMALIZED_COLUMN])
    op.create_unique_constraint(NEW_LIMITATION_UQ, LIMITATION_TABLE, ["disease_id", NORMALIZED_COLUMN])

    _assert_no_orphans(bind, TREATMENT_CONCEPT_TYPE, TREATMENT_TABLE)
    _assert_no_orphans(bind, LIMITATION_CONCEPT_TYPE, LIMITATION_TABLE)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    _drop_constraint_if_exists(
        bind,
        TREATMENT_TABLE,
        _resolve_unique_constraint_name(bind, TREATMENT_TABLE, ("disease_id", NORMALIZED_COLUMN), NEW_TREATMENT_UQ),
    )
    _drop_constraint_if_exists(
        bind,
        LIMITATION_TABLE,
        _resolve_unique_constraint_name(bind, LIMITATION_TABLE, ("disease_id", NORMALIZED_COLUMN), NEW_LIMITATION_UQ),
    )

    op.create_unique_constraint(
        OLD_TREATMENT_UQ,
        TREATMENT_TABLE,
        ["disease_id", "treatment_name", "treatment_category"],
    )
    op.create_unique_constraint(
        OLD_LIMITATION_UQ,
        LIMITATION_TABLE,
        ["disease_id", "limitation_name", "limitation_category"],
    )

    op.drop_index(op.f(f"ix_{TREATMENT_TABLE}_{NORMALIZED_COLUMN}"), table_name=TREATMENT_TABLE)
    op.drop_index(op.f(f"ix_{LIMITATION_TABLE}_{NORMALIZED_COLUMN}"), table_name=LIMITATION_TABLE)
    op.drop_column(TREATMENT_TABLE, NORMALIZED_COLUMN)
    op.drop_column(LIMITATION_TABLE, NORMALIZED_COLUMN)
