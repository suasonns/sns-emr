"""align_benefit_periods_table_to_current_model

Revision ID: 31d52818353a
Revises: 862e488b3504
Create Date: 2026-05-30 10:16:32.066348
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "31d52818353a"
down_revision: Union[str, Sequence[str], None] = "862e488b3504"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    result = conn.execute(
        sa.text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :table_name
              AND column_name = :column_name
            """
        ),
        {"table_name": table_name, "column_name": column_name},
    )
    return result.scalar() is not None


def _constraint_exists(conn, table_name: str, constraint_name: str) -> bool:
    result = conn.execute(
        sa.text(
            """
            SELECT 1
            FROM information_schema.table_constraints
            WHERE table_schema = 'public'
              AND table_name = :table_name
              AND constraint_name = :constraint_name
            """
        ),
        {"table_name": table_name, "constraint_name": constraint_name},
    )
    return result.scalar() is not None


def _index_exists(conn, table_name: str, index_name: str) -> bool:
    result = conn.execute(
        sa.text(
            """
            SELECT 1
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename = :table_name
              AND indexname = :index_name
            """
        ),
        {"table_name": table_name, "index_name": index_name},
    )
    return result.scalar() is not None


def upgrade() -> None:
    conn = op.get_bind()

    # ---------------------------------------------------------
    # 1. Add tenant_id if missing
    # ---------------------------------------------------------
    if not _column_exists(conn, "benefit_periods", "tenant_id"):
        op.add_column(
            "benefit_periods",
            sa.Column("tenant_id", sa.UUID(), nullable=True),
        )

    # ---------------------------------------------------------
    # 2. Add benefit_type if missing
    #    Use String first to avoid enum migration complexity in repair step.
    # ---------------------------------------------------------
    if not _column_exists(conn, "benefit_periods", "benefit_type"):
        op.add_column(
            "benefit_periods",
            sa.Column("benefit_type", sa.String(length=32), nullable=True),
        )

    # ---------------------------------------------------------
    # 3. Add period_number if missing
    # ---------------------------------------------------------
    if not _column_exists(conn, "benefit_periods", "period_number"):
        op.add_column(
            "benefit_periods",
            sa.Column("period_number", sa.Integer(), nullable=True),
        )

    # ---------------------------------------------------------
    # 4. Add election_date if missing
    # ---------------------------------------------------------
    if not _column_exists(conn, "benefit_periods", "election_date"):
        op.add_column(
            "benefit_periods",
            sa.Column("election_date", sa.Date(), nullable=True),
        )

    # ---------------------------------------------------------
    # 5. Add created_by if missing
    # ---------------------------------------------------------
    if not _column_exists(conn, "benefit_periods", "created_by"):
        op.add_column(
            "benefit_periods",
            sa.Column("created_by", sa.UUID(), nullable=True),
        )

    # ---------------------------------------------------------
    # 6. Backfill tenant_id from patients.tenant_id
    # ---------------------------------------------------------
    op.execute(
        """
        UPDATE benefit_periods bp
        SET tenant_id = p.tenant_id
        FROM patients p
        WHERE p.id = bp.patient_id
          AND bp.tenant_id IS NULL
        """
    )

    # ---------------------------------------------------------
    # 7. Backfill period_number from old benefit_number if present
    # ---------------------------------------------------------
    if _column_exists(conn, "benefit_periods", "benefit_number"):
        op.execute(
            """
            UPDATE benefit_periods
            SET period_number = benefit_number
            WHERE period_number IS NULL
              AND benefit_number IS NOT NULL
            """
        )

    # ---------------------------------------------------------
    # 8. Backfill election_date from start_date if missing
    #    This is a practical repair default for existing rows.
    # ---------------------------------------------------------
    op.execute(
        """
        UPDATE benefit_periods
        SET election_date = start_date
        WHERE election_date IS NULL
          AND start_date IS NOT NULL
        """
    )

    # ---------------------------------------------------------
    # 9. Backfill benefit_type from period_number
    #    1 = INITIAL
    #    2+ = RECERT
    # ---------------------------------------------------------
    op.execute(
        """
        UPDATE benefit_periods
        SET benefit_type = CASE
            WHEN period_number = 1 THEN 'INITIAL'
            ELSE 'RECERT'
        END
        WHERE benefit_type IS NULL
          AND period_number IS NOT NULL
        """
    )

    # ---------------------------------------------------------
    # 10. Set NOT NULL where current service/model expects it
    # ---------------------------------------------------------
    op.alter_column(
        "benefit_periods",
        "tenant_id",
        existing_type=sa.UUID(),
        nullable=False,
    )

    op.alter_column(
        "benefit_periods",
        "period_number",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.alter_column(
        "benefit_periods",
        "election_date",
        existing_type=sa.Date(),
        nullable=False,
    )

    op.alter_column(
        "benefit_periods",
        "benefit_type",
        existing_type=sa.String(length=32),
        nullable=False,
    )

    # ---------------------------------------------------------
    # 11. Add FK: tenant_id -> tenants.id
    # ---------------------------------------------------------
    if not _constraint_exists(conn, "benefit_periods", "fk_benefit_periods_tenant_id"):
        op.create_foreign_key(
            "fk_benefit_periods_tenant_id",
            "benefit_periods",
            "tenants",
            ["tenant_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # ---------------------------------------------------------
    # 12. Add FK: created_by -> users.id
    # ---------------------------------------------------------
    if not _constraint_exists(conn, "benefit_periods", "fk_benefit_periods_created_by"):
        op.create_foreign_key(
            "fk_benefit_periods_created_by",
            "benefit_periods",
            "users",
            ["created_by"],
            ["id"],
        )

    # ---------------------------------------------------------
    # 13. Add index for tenant_id
    # ---------------------------------------------------------
    if not _index_exists(conn, "benefit_periods", "ix_benefit_periods_tenant_id"):
        op.create_index(
            "ix_benefit_periods_tenant_id",
            "benefit_periods",
            ["tenant_id"],
        )

    # ---------------------------------------------------------
    # 14. Add index for period_number
    # ---------------------------------------------------------
    if not _index_exists(conn, "benefit_periods", "ix_benefit_periods_period_number"):
        op.create_index(
            "ix_benefit_periods_period_number",
            "benefit_periods",
            ["period_number"],
        )

    # ---------------------------------------------------------
    # 15. Add index for benefit_type
    # ---------------------------------------------------------
    if not _index_exists(conn, "benefit_periods", "ix_benefit_periods_benefit_type"):
        op.create_index(
            "ix_benefit_periods_benefit_type",
            "benefit_periods",
            ["benefit_type"],
        )


def downgrade() -> None:
    conn = op.get_bind()

    if _index_exists(conn, "benefit_periods", "ix_benefit_periods_benefit_type"):
        op.drop_index("ix_benefit_periods_benefit_type", table_name="benefit_periods")

    if _index_exists(conn, "benefit_periods", "ix_benefit_periods_period_number"):
        op.drop_index("ix_benefit_periods_period_number", table_name="benefit_periods")

    if _index_exists(conn, "benefit_periods", "ix_benefit_periods_tenant_id"):
        op.drop_index("ix_benefit_periods_tenant_id", table_name="benefit_periods")

    if _constraint_exists(conn, "benefit_periods", "fk_benefit_periods_created_by"):
        op.drop_constraint(
            "fk_benefit_periods_created_by",
            "benefit_periods",
            type_="foreignkey",
        )

    if _constraint_exists(conn, "benefit_periods", "fk_benefit_periods_tenant_id"):
        op.drop_constraint(
            "fk_benefit_periods_tenant_id",
            "benefit_periods",
            type_="foreignkey",
        )

    if _column_exists(conn, "benefit_periods", "created_by"):
        op.drop_column("benefit_periods", "created_by")

    if _column_exists(conn, "benefit_periods", "election_date"):
        op.drop_column("benefit_periods", "election_date")

    if _column_exists(conn, "benefit_periods", "period_number"):
        op.drop_column("benefit_periods", "period_number")

    if _column_exists(conn, "benefit_periods", "benefit_type"):
        op.drop_column("benefit_periods", "benefit_type")

    if _column_exists(conn, "benefit_periods", "tenant_id"):
        op.drop_column("benefit_periods", "tenant_id")