"""repair idg intelligence communication log fields

Revision ID: 166f835f4ab8
Revises: 0aed5dcae0b4
Create Date: 2026-07-31 12:38:55.157063

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '166f835f4ab8'
down_revision: Union[str, Sequence[str], None] = '0aed5dcae0b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


"""repair idg intelligence communication log fields

Revision ID: REPLACE_WITH_NEW_REVISION
Revises: REPLACE_WITH_CURRENT_HEAD
Create Date: 2026-07-31

Purpose:
- Bring manually created idg_intelligence_items into Alembic control if needed.
- Add communication-log harvest fields for IDG visibility.
- Backfill existing communications_logs into idg_intelligence_items.
- Preserve CHHA/staff/family/facility/hospital/MD office/lab reports as observation intelligence.
"""


TABLE_NAME = "idg_intelligence_items"


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names(schema="public")


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    if table_name not in inspector.get_table_names(schema="public"):
        return False

    columns = inspector.get_columns(table_name, schema="public")
    return any(column["name"] == column_name for column in columns)


def _index_exists(index_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _table_exists(TABLE_NAME):
        return False

    indexes = inspector.get_indexes(TABLE_NAME, schema="public")
    return any(index["name"] == index_name for index in indexes)


def _constraint_exists(table_name: str, constraint_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)

    if table_name not in inspector.get_table_names(schema="public"):
        return False

    unique_constraints = inspector.get_unique_constraints(table_name, schema="public")
    if any(constraint["name"] == constraint_name for constraint in unique_constraints):
        return True

    check_constraints = inspector.get_check_constraints(table_name, schema="public")
    if any(constraint["name"] == constraint_name for constraint in check_constraints):
        return True

    foreign_keys = inspector.get_foreign_keys(table_name, schema="public")
    if any(constraint["name"] == constraint_name for constraint in foreign_keys):
        return True

    return False


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not _column_exists(table_name, column.name):
        op.add_column(table_name, column)


def _create_index_if_missing(index_name: str, columns: list[str]) -> None:
    if not _index_exists(index_name):
        op.create_index(index_name, TABLE_NAME, columns)


def upgrade() -> None:
    # ------------------------------------------------------------
    # 1. Ensure idg_intelligence_items exists.
    #    This supports environments where the table was first
    #    created manually in pgAdmin before Alembic was updated.
    # ------------------------------------------------------------

    if not _table_exists(TABLE_NAME):
        op.create_table(
            TABLE_NAME,
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),

            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("benefit_period_id", postgresql.UUID(as_uuid=True), nullable=True),

            sa.Column("source_type", sa.String(length=64), nullable=False),
            sa.Column("source_table", sa.String(length=128), nullable=False),
            sa.Column("source_record_id", postgresql.UUID(as_uuid=True), nullable=False),

            sa.Column("source_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("source_discipline", sa.String(length=50), nullable=True),
            sa.Column("source_author_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("source_author_name", sa.String(length=255), nullable=True),

            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("original_excerpt", sa.Text(), nullable=True),

            sa.Column("category", sa.String(length=100), nullable=True),
            sa.Column("severity", sa.String(length=50), nullable=True),
            sa.Column("confidence", sa.String(length=50), nullable=True),

            sa.Column(
                "requires_idg_discussion",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column(
                "discussion_status",
                sa.String(length=50),
                nullable=False,
                server_default=sa.text("'PENDING'"),
            ),

            sa.Column("idg_review_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("idg_meeting_id", postgresql.UUID(as_uuid=True), nullable=True),

            sa.Column("discussed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("discussed_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("disposition", sa.String(length=50), nullable=True),
            sa.Column("idg_summary", sa.Text(), nullable=True),

            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),

            sa.UniqueConstraint(
                "source_table",
                "source_record_id",
                name="uq_idg_intelligence_source",
            ),
        )

    # ------------------------------------------------------------
    # 2. Add communication-log harvest metadata fields.
    # ------------------------------------------------------------

    _add_column_if_missing(
        TABLE_NAME,
        sa.Column("communication_log_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    _add_column_if_missing(
        TABLE_NAME,
        sa.Column("communication_event_type", sa.String(length=100), nullable=True),
    )

    _add_column_if_missing(
        TABLE_NAME,
        sa.Column("communication_focus_area", sa.String(length=100), nullable=True),
    )

    _add_column_if_missing(
        TABLE_NAME,
        sa.Column("communication_event_time", sa.DateTime(timezone=True), nullable=True),
    )

    _add_column_if_missing(
        TABLE_NAME,
        sa.Column("communication_received_at", sa.DateTime(timezone=True), nullable=True),
    )

    _add_column_if_missing(
        TABLE_NAME,
        sa.Column("communication_status", sa.String(length=50), nullable=True),
    )

    _add_column_if_missing(
        TABLE_NAME,
        sa.Column("communication_summary", sa.Text(), nullable=True),
    )

    _add_column_if_missing(
        TABLE_NAME,
        sa.Column("communication_details", postgresql.JSONB(), nullable=True),
    )

    # Who reported the concern.
    # Examples: family, caregiver, CHHA, RN, LVN, MSW, SC, facility, hospital, MD office, lab.
    _add_column_if_missing(
        TABLE_NAME,
        sa.Column("reported_by_name", sa.String(length=255), nullable=True),
    )

    _add_column_if_missing(
        TABLE_NAME,
        sa.Column("reported_by_role", sa.String(length=100), nullable=True),
    )

    _add_column_if_missing(
        TABLE_NAME,
        sa.Column("reported_by_discipline", sa.String(length=100), nullable=True),
    )

    _add_column_if_missing(
        TABLE_NAME,
        sa.Column("reported_source_type", sa.String(length=100), nullable=True),
    )

    _add_column_if_missing(
        TABLE_NAME,
        sa.Column("reporting_organization", sa.String(length=255), nullable=True),
    )

    # Who received or entered the communication.
    _add_column_if_missing(
        TABLE_NAME,
        sa.Column("received_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    _add_column_if_missing(
        TABLE_NAME,
        sa.Column("received_by_name", sa.String(length=255), nullable=True),
    )

    _add_column_if_missing(
        TABLE_NAME,
        sa.Column("received_by_discipline", sa.String(length=100), nullable=True),
    )

    # Critical result support, especially lab calls.
    _add_column_if_missing(
        TABLE_NAME,
        sa.Column(
            "is_critical_result",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    _add_column_if_missing(
        TABLE_NAME,
        sa.Column("critical_result_summary", sa.Text(), nullable=True),
    )

    # Why this communication was harvested for IDG.
    _add_column_if_missing(
        TABLE_NAME,
        sa.Column("harvest_reason", sa.Text(), nullable=True),
    )

    _add_column_if_missing(
        TABLE_NAME,
        sa.Column(
            "requires_followup",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    _add_column_if_missing(
        TABLE_NAME,
        sa.Column("source_priority", sa.String(length=50), nullable=True),
    )

    # ------------------------------------------------------------
    # 3. Optional foreign key for communication_log_id.
    #    This is nullable and only applies to COMMUNICATION_LOG items.
    # ------------------------------------------------------------

    if _table_exists("communications_logs"):
        if not _constraint_exists(TABLE_NAME, "fk_idg_intelligence_communication_log"):
            op.create_foreign_key(
                "fk_idg_intelligence_communication_log",
                TABLE_NAME,
                "communications_logs",
                ["communication_log_id"],
                ["id"],
                ondelete="RESTRICT",
            )

    # ------------------------------------------------------------
    # 4. Indexes for IDG communication-log review.
    # ------------------------------------------------------------

    _create_index_if_missing(
        "ix_idg_intelligence_comm_log_id",
        ["communication_log_id"],
    )

    _create_index_if_missing(
        "ix_idg_intelligence_comm_event_time",
        ["tenant_id", "patient_id", "communication_event_time"],
    )

    _create_index_if_missing(
        "ix_idg_intelligence_reported_source_type",
        ["tenant_id", "reported_source_type"],
    )

    _create_index_if_missing(
        "ix_idg_intelligence_received_by",
        ["tenant_id", "received_by_user_id"],
    )

    _create_index_if_missing(
        "ix_idg_intelligence_discussion_status",
        ["tenant_id", "discussion_status"],
    )

    # ------------------------------------------------------------
    # 5. Backfill existing communications_logs into IDG intelligence.
    #    All patient-specific communication logs are harvested.
    #    The item remains observational. IDG performs interpretation.
    # ------------------------------------------------------------

    if _table_exists("communications_logs"):
        op.execute(
            """
            INSERT INTO idg_intelligence_items (
                tenant_id,
                patient_id,
                source_type,
                source_table,
                source_record_id,

                source_date,
                source_author_id,
                title,
                summary,
                original_excerpt,
                category,

                requires_idg_discussion,
                discussion_status,

                communication_log_id,
                communication_event_type,
                communication_focus_area,
                communication_event_time,
                communication_received_at,
                communication_status,
                communication_summary,
                communication_details,

                received_by_user_id,

                reported_source_type,
                harvest_reason,
                requires_followup,
                source_priority,

                created_at,
                updated_at
            )
            SELECT
                c.tenant_id,
                c.patient_id,
                'COMMUNICATION_LOG',
                'communications_logs',
                c.id,

                c.event_time,
                c.created_by,
                LEFT(
                    COALESCE(NULLIF(c.event_type, ''), 'Communication Log')
                    ||
                    CASE
                        WHEN c.focus_area IS NOT NULL AND c.focus_area <> ''
                        THEN ' - ' || c.focus_area
                        ELSE ''
                    END,
                    255
                ) AS title,
                c.summary,
                c.summary,
                c.focus_area,

                true,
                'PENDING',

                c.id,
                c.event_type,
                c.focus_area,
                c.event_time,
                c.created_at,
                c.status,
                c.summary,
                c.details::jsonb,

                c.created_by,

                CASE
                    WHEN c.event_type ILIKE '%family%' THEN 'FAMILY'
                    WHEN c.event_type ILIKE '%caregiver%' THEN 'CAREGIVER'
                    WHEN c.event_type ILIKE '%facility%' THEN 'FACILITY'
                    WHEN c.event_type ILIKE '%hospital%' THEN 'HOSPITAL'
                    WHEN c.event_type ILIKE '%physician%' THEN 'MD_OFFICE'
                    WHEN c.event_type ILIKE '%doctor%' THEN 'MD_OFFICE'
                    WHEN c.event_type ILIKE '%lab%' THEN 'LAB'
                    WHEN c.event_type ILIKE '%staff%' THEN 'STAFF'
                    WHEN c.event_type ILIKE '%chha%' THEN 'STAFF'
                    WHEN c.event_type ILIKE '%rn%' THEN 'STAFF'
                    WHEN c.event_type ILIKE '%lvn%' THEN 'STAFF'
                    WHEN c.event_type ILIKE '%msw%' THEN 'STAFF'
                    WHEN c.event_type ILIKE '%sc%' THEN 'STAFF'
                    ELSE 'OTHER'
                END AS reported_source_type,

                'Communication log harvested for IDG visibility because all patient-specific reports must be available for interdisciplinary review.',

                CASE
                    WHEN c.summary ILIKE '%critical%'
                      OR c.summary ILIKE '%fall%'
                      OR c.summary ILIKE '%hospital%'
                      OR c.summary ILIKE '%er %'
                      OR c.summary ILIKE '%emergency%'
                      OR c.summary ILIKE '%skin%'
                      OR c.summary ILIKE '%wound%'
                      OR c.summary ILIKE '%pain%'
                      OR c.summary ILIKE '%medication%'
                      OR c.summary ILIKE '%confusion%'
                      OR c.summary ILIKE '%decline%'
                      OR c.summary ILIKE '%poor intake%'
                      OR c.summary ILIKE '%not eating%'
                      OR c.summary ILIKE '%shortness of breath%'
                      OR c.summary ILIKE '%sob%'
                    THEN true
                    ELSE false
                END AS requires_followup,

                CASE
                    WHEN c.summary ILIKE '%critical%'
                      OR c.event_type ILIKE '%critical%'
                      OR c.summary ILIKE '%emergency%'
                      OR c.summary ILIKE '%hospital%'
                      OR c.summary ILIKE '%er %'
                    THEN 'HIGH'
                    ELSE 'NORMAL'
                END AS source_priority,

                NOW(),
                NOW()
            FROM communications_logs c
            ON CONFLICT (source_table, source_record_id)
            DO UPDATE SET
                communication_log_id = EXCLUDED.communication_log_id,
                communication_event_type = EXCLUDED.communication_event_type,
                communication_focus_area = EXCLUDED.communication_focus_area,
                communication_event_time = EXCLUDED.communication_event_time,
                communication_received_at = EXCLUDED.communication_received_at,
                communication_status = EXCLUDED.communication_status,
                communication_summary = EXCLUDED.communication_summary,
                communication_details = EXCLUDED.communication_details,
                received_by_user_id = EXCLUDED.received_by_user_id,
                reported_source_type = EXCLUDED.reported_source_type,
                harvest_reason = EXCLUDED.harvest_reason,
                requires_followup = EXCLUDED.requires_followup,
                source_priority = EXCLUDED.source_priority,
                updated_at = NOW();
            """
        )


def downgrade() -> None:
    # Forward-only production posture:
    # Do not depend on downgrade for production rollback.
    # This downgrade is provided only for local development reversal.

    if not _table_exists(TABLE_NAME):
        return

    for index_name in [
        "ix_idg_intelligence_received_by",
        "ix_idg_intelligence_reported_source_type",
        "ix_idg_intelligence_comm_event_time",
        "ix_idg_intelligence_comm_log_id",
    ]:
        if _index_exists(index_name):
            op.drop_index(index_name, table_name=TABLE_NAME)

    if _constraint_exists(TABLE_NAME, "fk_idg_intelligence_communication_log"):
        op.drop_constraint(
            "fk_idg_intelligence_communication_log",
            TABLE_NAME,
            type_="foreignkey",
        )

    columns_to_drop = [
        "source_priority",
        "requires_followup",
        "harvest_reason",
        "critical_result_summary",
        "is_critical_result",
        "received_by_discipline",
        "received_by_name",
        "received_by_user_id",
        "reporting_organization",
        "reported_source_type",
        "reported_by_discipline",
        "reported_by_role",
        "reported_by_name",
        "communication_details",
        "communication_summary",
        "communication_status",
        "communication_received_at",
        "communication_event_time",
        "communication_focus_area",
        "communication_event_type",
        "communication_log_id",
    ]

    for column_name in columns_to_drop:
        if _column_exists(TABLE_NAME, column_name):
            op.drop_column(TABLE_NAME, column_name)
