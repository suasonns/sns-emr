"""wire allergies into patient_face_sheet_view

Revision ID: ccff1034bff9
Revises: 2e9fb87a7c53
Create Date: 2026-05-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect, text

# revision identifiers, used by Alembic.
revision: str = "ccff1034bff9"
down_revision: Union[str, Sequence[str], None] = "2e9fb87a7c53"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    bind = op.get_bind()
    insp = inspect(bind)

    # Ensure UUID generator is available
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # ----------------------------------------------------
    # 1) Allergy tables (FKs -> users.id; accounts not created yet)
    # ----------------------------------------------------
    if not insp.has_table("patient_allergy_profiles"):
        op.create_table(
            "patient_allergy_profiles",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "patient_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("patients.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            sa.Column(
                "is_nkda",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column(
                "last_updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                # keep *_account_id naming for future accounts refactor
                "last_updated_by_account_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id"),
                nullable=True,
            ),
        )

    if not insp.has_table("patient_allergies"):
        op.create_table(
            "patient_allergies",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "patient_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("patients.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("allergy_name", sa.Text(), nullable=False),
            sa.Column("reaction", sa.Text(), nullable=True),
            sa.Column("severity", sa.Text(), nullable=True),
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column(
                "recorded_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "recorded_by_account_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id"),
                nullable=True,
            ),
        )

        op.create_index(
            "ix_patient_allergies_patient_active",
            "patient_allergies",
            ["patient_id", "is_active"],
        )

    # ----------------------------------------------------
    # 2) Create face sheet view safely:
    #    DROP first (prevents "cannot drop columns from view")
    #    then CREATE with a stable column set.
    # ----------------------------------------------------

    patient_cols = {c["name"] for c in insp.get_columns("patients")}
    dx_cols = {c["name"] for c in insp.get_columns("diagnosis_sources")}

    # Patient column selectors (NULL if missing)
    mrn_expr = "p.mrn" if "mrn" in patient_cols else "NULL::text"
    last_name_expr = "p.last_name" if "last_name" in patient_cols else "NULL::text"
    first_name_expr = "p.first_name" if "first_name" in patient_cols else "NULL::text"
    dob_expr = "p.date_of_birth" if "date_of_birth" in patient_cols else "NULL::date"

    has_status = "status" in patient_cols
    status_expr = "p.status" if has_status else "NULL::text"
    admitted_expr = "(p.status = 'ACTIVE')" if has_status else "false"

    age_expr = (
        "DATE_PART('year', AGE(CURRENT_DATE, p.date_of_birth))::int"
        if "date_of_birth" in patient_cols
        else "NULL::int"
    )

    # Diagnosis actor column (normalize to a single alias actor_id)
    if "documented_by_account_id" in dx_cols:
        actor_col = "documented_by_account_id"
    elif "documented_by_user_id" in dx_cols:
        actor_col = "documented_by_user_id"
    else:
        actor_col = None

    rn_actor_select = f"ds.{actor_col} AS actor_id" if actor_col else "NULL::uuid AS actor_id"

    view_sql = f"""
    DROP VIEW IF EXISTS patient_face_sheet_view;

    CREATE VIEW patient_face_sheet_view AS
    SELECT
      p.id AS patient_id,
      {mrn_expr} AS mrn,
      {last_name_expr} AS last_name,
      {first_name_expr} AS first_name,
      {dob_expr} AS date_of_birth,
      {age_expr} AS age,
      {status_expr} AS patient_status,
      {admitted_expr} AS is_admitted,

      -- Primary Dx (RN-first for admitted; referral for non-admits)
      CASE
        WHEN {admitted_expr}
          THEN COALESCE(rn_primary.description, referral_primary.description)
        ELSE referral_primary.description
      END AS primary_dx_description,

      CASE
        WHEN {admitted_expr}
          THEN COALESCE(rn_primary.icd_code, referral_primary.icd_code)
        ELSE referral_primary.icd_code
      END AS primary_dx_icd,

      CASE
        WHEN {admitted_expr} AND rn_primary.description IS NOT NULL THEN 'RN_IA'
        WHEN referral_primary.description IS NOT NULL THEN 'REFERRAL'
        ELSE NULL
      END AS primary_dx_source,

      rn_primary.documented_at AS primary_dx_updated_at,
      rn_primary.actor_id AS primary_dx_updated_by_account_id,

      rn_other.related_dx_list,
      rn_other.secondary_dx_list,

      referral_primary.description AS referral_primary_dx_description,
      cti_primary.description AS cti_primary_dx_description,

      -- Allergy state (compliance-critical)
      CASE
        WHEN COALESCE(ap.is_nkda, false) = true THEN 'NKDA'
        WHEN COALESCE(allergy_agg.allergy_count, 0) > 0 THEN 'HAS_ALLERGY'
        ELSE 'NOT_DOCUMENTED'
      END AS allergy_state,

      allergy_agg.allergy_list AS allergy_list,
      ap.last_updated_at AS allergy_last_updated,

      disc.id AS dx_discrepancy_id,
      disc.status AS dx_discrepancy_status,
      (disc.status = 'OPEN') AS dx_discrepancy_open

    FROM patients p

    -- RN primary (single row)
    LEFT JOIN LATERAL (
      SELECT
        ds.description,
        ds.icd_code,
        ds.documented_at,
        {rn_actor_select}
      FROM diagnosis_sources ds
      WHERE ds.patient_id = p.id
        AND ds.source = 'RN_IA'
        AND ds.dx_type = 'PRIMARY'
        AND ds.is_active = true
      ORDER BY ds.documented_at DESC
      LIMIT 1
    ) rn_primary ON true

    -- RN related + secondary (aggregated in lateral)
    LEFT JOIN LATERAL (
      SELECT
        STRING_AGG(DISTINCT ds.description, ', ' ORDER BY ds.description)
          FILTER (WHERE ds.dx_type = 'RELATED') AS related_dx_list,
        STRING_AGG(DISTINCT ds.description, ', ' ORDER BY ds.description)
          FILTER (WHERE ds.dx_type = 'SECONDARY') AS secondary_dx_list
      FROM diagnosis_sources ds
      WHERE ds.patient_id = p.id
        AND ds.source = 'RN_IA'
        AND ds.dx_type IN ('RELATED','SECONDARY')
        AND ds.is_active = true
    ) rn_other ON true

    -- Referral primary (single row)
    LEFT JOIN LATERAL (
      SELECT ds.description, ds.icd_code
      FROM diagnosis_sources ds
      WHERE ds.patient_id = p.id
        AND ds.source = 'REFERRAL'
        AND ds.dx_type = 'PRIMARY'
        AND ds.is_active = true
      ORDER BY ds.documented_at DESC
      LIMIT 1
    ) referral_primary ON true

    -- CTI primary (single row)
    LEFT JOIN LATERAL (
      SELECT ds.description, ds.icd_code
      FROM diagnosis_sources ds
      WHERE ds.patient_id = p.id
        AND ds.source = 'CTI'
        AND ds.dx_type = 'PRIMARY'
        AND ds.is_active = true
      ORDER BY ds.documented_at DESC
      LIMIT 1
    ) cti_primary ON true

    -- Allergy profile (single row per patient)
    LEFT JOIN patient_allergy_profiles ap
      ON ap.patient_id = p.id

    -- Allergy list/count (aggregated in lateral)
    LEFT JOIN LATERAL (
      SELECT
        COUNT(*) FILTER (WHERE pa.is_active = true) AS allergy_count,
        STRING_AGG(pa.allergy_name, ', ' ORDER BY pa.allergy_name)
          FILTER (WHERE pa.is_active = true) AS allergy_list
      FROM patient_allergies pa
      WHERE pa.patient_id = p.id
    ) allergy_agg ON true

    -- Latest discrepancy (single row)
    LEFT JOIN LATERAL (
      SELECT d.id, d.status
      FROM diagnosis_discrepancies d
      WHERE d.patient_id = p.id
      ORDER BY d.created_at DESC
      LIMIT 1
    ) disc ON true
    ;
    """

    op.execute(text(view_sql))


def downgrade():
    op.execute("DROP VIEW IF EXISTS patient_face_sheet_view;")