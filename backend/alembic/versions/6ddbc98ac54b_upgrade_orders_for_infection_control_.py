"""upgrade orders for infection control and audits

Forward-only, repair-safe migration.

Purpose:
- Preserve existing orders table
- Add missing audit / infection-control columns safely
- Create diagnoses table only if missing
- Only index diagnoses if THIS migration created it
- Avoid privilege failures on manually created tables owned by another role
- Remain safe even if a column was added manually before Alembic runs
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "6ddbc98ac54b"
down_revision: Union[str, Sequence[str], None] = "5204791f4c4a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "public"
UUID = postgresql.UUID(as_uuid=True)


def _bind():
    return op.get_bind()


def _inspector():
    return sa.inspect(_bind())


def _table_exists(table_name: str) -> bool:
    inspector = _inspector()
    return table_name in set(inspector.get_table_names(schema=SCHEMA))


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = _inspector()
    return column_name in {
        c["name"] for c in inspector.get_columns(table_name, schema=SCHEMA)
    }


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = _inspector()
    return index_name in {
        ix["name"] for ix in inspector.get_indexes(table_name, schema=SCHEMA)
    }


def _foreign_key_exists(table_name: str, fk_name: str) -> bool:
    inspector = _inspector()
    return fk_name in {
        fk["name"]
        for fk in inspector.get_foreign_keys(table_name, schema=SCHEMA)
        if fk.get("name")
    }


def _check_exists(table_name: str, ck_name: str) -> bool:
    inspector = _inspector()
    return ck_name in {
        ck["name"]
        for ck in inspector.get_check_constraints(table_name, schema=SCHEMA)
        if ck.get("name")
    }


def _current_context() -> dict:
    bind = _bind()
    row = bind.execute(
        sa.text(
            """
            SELECT
                current_user AS current_user,
                session_user AS session_user,
                current_database() AS current_database,
                current_schema() AS current_schema,
                current_setting('search_path') AS search_path,
                (
                    SELECT rolsuper
                    FROM pg_roles
                    WHERE rolname = current_user
                ) AS is_superuser
            """
        )
    ).mappings().one()

    return dict(row)


def _table_owner(table_name: str) -> str | None:
    bind = _bind()
    row = bind.execute(
        sa.text(
            """
            SELECT tableowner
            FROM pg_tables
            WHERE schemaname = :schema_name
              AND tablename = :table_name
            """
        ),
        {"schema_name": SCHEMA, "table_name": table_name},
    ).scalar_one_or_none()

    return row


def _assert_can_alter(table_name: str) -> None:
    """
    Fail fast with a clear message if this connection cannot ALTER the target table.
    This is much more diagnosable than letting PostgreSQL fail deep in op.add_column().
    """
    if not _table_exists(table_name):
        return

    ctx = _current_context()
    owner = _table_owner(table_name)

    if owner is None:
        return

    if ctx["is_superuser"]:
        return

    if ctx["current_user"] != owner:
        raise RuntimeError(
            (
                f"Cannot alter {SCHEMA}.{table_name}: "
                f"current_user={ctx['current_user']} "
                f"session_user={ctx['session_user']} "
                f"owner={owner} "
                f"database={ctx['current_database']} "
                f"schema={ctx['current_schema']} "
                f"search_path={ctx['search_path']}"
            )
        )


def upgrade():
    bind = _bind()
    created_diagnoses = False

    # ------------------------------------------------------------------
    # 0) Preflight context
    # ------------------------------------------------------------------
    # We only need alter rights on orders, because diagnoses is only modified
    # if this migration creates it.
    _assert_can_alter("orders")

    # ------------------------------------------------------------------
    # 1) Create diagnoses table ONLY if missing
    # ------------------------------------------------------------------
    if not _table_exists("diagnoses"):
        op.create_table(
            "diagnoses",
            sa.Column("id", UUID, primary_key=True, nullable=False),
            sa.Column("patient_id", UUID, nullable=False),
            sa.Column("diagnosis_name", sa.Text(), nullable=False),
            sa.Column("onset_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column(
                "infection_source",
                sa.Text(),
                nullable=False,
                server_default=sa.text("'UNKNOWN'"),
            ),
            # PRESENT_ON_ADMISSION / ACQUIRED_UNDER_SERVICE / UNKNOWN
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_by", UUID, nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.CheckConstraint(
                "infection_source IN ('PRESENT_ON_ADMISSION','ACQUIRED_UNDER_SERVICE','UNKNOWN')",
                name="ck_diagnoses_infection_source",
            ),
            schema=SCHEMA,
        )
        created_diagnoses = True

    # Only create indexes on diagnoses if THIS migration created the table.
    if created_diagnoses:
        if not _index_exists("diagnoses", "ix_diagnoses_patient_id"):
            op.create_index(
                "ix_diagnoses_patient_id",
                "diagnoses",
                ["patient_id"],
                schema=SCHEMA,
            )

        if not _index_exists("diagnoses", "ix_diagnoses_onset_date"):
            op.create_index(
                "ix_diagnoses_onset_date",
                "diagnoses",
                ["onset_date"],
                schema=SCHEMA,
            )

        if not _index_exists("diagnoses", "ix_diagnoses_infection_source"):
            op.create_index(
                "ix_diagnoses_infection_source",
                "diagnoses",
                ["infection_source"],
                schema=SCHEMA,
            )

    # ------------------------------------------------------------------
    # 2) Upgrade orders table if it exists
    # ------------------------------------------------------------------
    if _table_exists("orders"):
        # ---- normalized query / audit columns ----
        if not _column_exists("orders", "order_category"):
            op.add_column(
                "orders",
                sa.Column("order_category", sa.Text(), nullable=True),
                schema=SCHEMA,
            )
            # MEDICATION / TREATMENT / DME / OTHER

        if not _column_exists("orders", "order_name"):
            op.add_column(
                "orders",
                sa.Column("order_name", sa.Text(), nullable=True),
                schema=SCHEMA,
            )

        if not _column_exists("orders", "medication_class"):
            op.add_column(
                "orders",
                sa.Column("medication_class", sa.Text(), nullable=True),
                schema=SCHEMA,
            )
            # ANTIBIOTIC / PAIN / ANXIOLYTIC / etc.

        if not _column_exists("orders", "indication"):
            op.add_column(
                "orders",
                sa.Column("indication", sa.Text(), nullable=True),
                schema=SCHEMA,
            )
            # UTI / PNEUMONIA / WOUND / etc.

        if not _column_exists("orders", "diagnosis_id"):
            op.add_column(
                "orders",
                sa.Column("diagnosis_id", UUID, nullable=True),
                schema=SCHEMA,
            )

        # ---- status / discontinuation audit ----
        if not _column_exists("orders", "status"):
            op.add_column(
                "orders",
                sa.Column(
                    "status",
                    sa.Text(),
                    nullable=False,
                    server_default=sa.text("'ACTIVE'"),
                ),
                schema=SCHEMA,
            )

        if not _column_exists("orders", "discontinued_at"):
            op.add_column(
                "orders",
                sa.Column("discontinued_at", sa.DateTime(timezone=True), nullable=True),
                schema=SCHEMA,
            )

        if not _column_exists("orders", "discontinued_by"):
            op.add_column(
                "orders",
                sa.Column("discontinued_by", UUID, nullable=True),
                schema=SCHEMA,
            )

        if not _column_exists("orders", "discontinued_reason"):
            op.add_column(
                "orders",
                sa.Column("discontinued_reason", sa.Text(), nullable=True),
                schema=SCHEMA,
            )

        # ---- ordering / signing audit ----
        if not _column_exists("orders", "ordered_by"):
            op.add_column(
                "orders",
                sa.Column("ordered_by", UUID, nullable=True),
                schema=SCHEMA,
            )

        if not _column_exists("orders", "ordered_at"):
            op.add_column(
                "orders",
                sa.Column("ordered_at", sa.DateTime(timezone=True), nullable=True),
                schema=SCHEMA,
            )

        if not _column_exists("orders", "signed_by"):
            op.add_column(
                "orders",
                sa.Column("signed_by", UUID, nullable=True),
                schema=SCHEMA,
            )

        if not _column_exists("orders", "signed_at"):
            op.add_column(
                "orders",
                sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
                schema=SCHEMA,
            )

        # ---- optional structured medication / oxygen support ----
        if not _column_exists("orders", "route"):
            op.add_column(
                "orders",
                sa.Column("route", sa.Text(), nullable=True),
                schema=SCHEMA,
            )

        if not _column_exists("orders", "dose"):
            op.add_column(
                "orders",
                sa.Column("dose", sa.Text(), nullable=True),
                schema=SCHEMA,
            )

        if not _column_exists("orders", "unit"):
            op.add_column(
                "orders",
                sa.Column("unit", sa.Text(), nullable=True),
                schema=SCHEMA,
            )

        if not _column_exists("orders", "frequency"):
            op.add_column(
                "orders",
                sa.Column("frequency", sa.Text(), nullable=True),
                schema=SCHEMA,
            )

        # ---- backfill active status if needed ----
        if _column_exists("orders", "status"):
            bind.execute(
                sa.text(
                    """
                    UPDATE public.orders
                    SET status = 'ACTIVE'
                    WHERE status IS NULL
                    """
                )
            )

        # ---- optional heuristic: infer MEDICATION if medication_class already present
        if _column_exists("orders", "order_category") and _column_exists("orders", "medication_class"):
            bind.execute(
                sa.text(
                    """
                    UPDATE public.orders
                    SET order_category = 'MEDICATION'
                    WHERE order_category IS NULL
                      AND medication_class IS NOT NULL
                    """
                )
            )

    # ------------------------------------------------------------------
    # 3) Add constraints / indexes on orders
    # ------------------------------------------------------------------
    if _table_exists("orders"):
        if _column_exists("orders", "status") and not _check_exists("orders", "ck_orders_status"):
            op.create_check_constraint(
                "ck_orders_status",
                "orders",
                "status IN ('ACTIVE','DISCONTINUED','COMPLETED')",
                schema=SCHEMA,
            )

        if _column_exists("orders", "order_category") and not _check_exists("orders", "ck_orders_order_category"):
            op.create_check_constraint(
                "ck_orders_order_category",
                "orders",
                "order_category IS NULL OR order_category IN ('MEDICATION','TREATMENT','DME','OTHER')",
                schema=SCHEMA,
            )

        if _column_exists("orders", "patient_id") and not _index_exists("orders", "ix_orders_patient_id"):
            op.create_index(
                "ix_orders_patient_id",
                "orders",
                ["patient_id"],
                schema=SCHEMA,
            )

        if _column_exists("orders", "status") and not _index_exists("orders", "ix_orders_status"):
            op.create_index(
                "ix_orders_status",
                "orders",
                ["status"],
                schema=SCHEMA,
            )

        if _column_exists("orders", "order_category") and not _index_exists("orders", "ix_orders_order_category"):
            op.create_index(
                "ix_orders_order_category",
                "orders",
                ["order_category"],
                schema=SCHEMA,
            )

        if _column_exists("orders", "medication_class") and not _index_exists("orders", "ix_orders_medication_class"):
            op.create_index(
                "ix_orders_medication_class",
                "orders",
                ["medication_class"],
                schema=SCHEMA,
            )

        if _column_exists("orders", "start_date") and not _index_exists("orders", "ix_orders_start_date"):
            op.create_index(
                "ix_orders_start_date",
                "orders",
                ["start_date"],
                schema=SCHEMA,
            )

        if _column_exists("orders", "discontinued_at") and not _index_exists("orders", "ix_orders_discontinued_at"):
            op.create_index(
                "ix_orders_discontinued_at",
                "orders",
                ["discontinued_at"],
                schema=SCHEMA,
            )

        if _column_exists("orders", "diagnosis_id") and not _index_exists("orders", "ix_orders_diagnosis_id"):
            op.create_index(
                "ix_orders_diagnosis_id",
                "orders",
                ["diagnosis_id"],
                schema=SCHEMA,
            )

    # ------------------------------------------------------------------
    # 4) Add FK ONLY if diagnoses was created here
    # ------------------------------------------------------------------
    # Since diagnoses may already have existed before Alembic touched it,
    # we only auto-create FK when diagnoses was created by this migration.
    if (
        created_diagnoses
        and _table_exists("orders")
        and _table_exists("diagnoses")
        and _column_exists("orders", "diagnosis_id")
        and not _foreign_key_exists("orders", "fk_orders_diagnosis")
    ):
        op.create_foreign_key(
            "fk_orders_diagnosis",
            "orders",
            "diagnoses",
            ["diagnosis_id"],
            ["id"],
            source_schema=SCHEMA,
            referent_schema=SCHEMA,
            ondelete="SET NULL",
        )


def downgrade():
    # Forward-only migration by design.
    pass