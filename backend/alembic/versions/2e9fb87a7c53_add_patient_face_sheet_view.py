"""add patient_face_sheet_view

Revision ID: 2e9fb87a7c53
Revises: 87234fede1d3
Create Date: 2026-05-06
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect, text

# revision identifiers, used by Alembic.
revision: str = "2e9fb87a7c53"
down_revision: Union[str, Sequence[str], None] = "87234fede1d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    bind = op.get_bind()
    insp = inspect(bind)

    # -------------------------
    # Detect tables / columns safely (avoids schema drift issues)
    # -------------------------
    has_patients = insp.has_table("patients")
    has_dx_sources = insp.has_table("diagnosis_sources")
    has_dx_disc = insp.has_table("diagnosis_discrepancies")
    has_allergies = insp.has_table("patient_allergies")

    if not (has_patients and has_dx_sources):
        raise RuntimeError("Cannot create patient_face_sheet_view: missing required tables (patients, diagnosis_sources).")

    patient_cols = {c["name"] for c in insp.get_columns("patients")}
    dx_cols = {c["name"] for c in insp.get_columns("diagnosis_sources")}

    # Optional columns in patients
    has_patient_status = "status" in patient_cols
    has_patient_mrn = "mrn" in patient_cols
    has_patient_dob = "date_of_birth" in patient_cols
    has_patient_last = "last_name" in patient_cols
    has_patient_first = "first_name" in patient_cols

    # Who documented the diagnosis (supports both historical naming variants)
    documented_by_col = None
    if "documented_by_account_id" in dx_cols:
        documented_by_col = "documented_by_account_id"
    elif "documented_by_user_id" in dx_cols:
        documented_by_col = "documented_by_user_id"

    # Allergies columns (supports variants)
    allergy_cols = set()
    if has_allergies:
        allergy_cols = {c["name"] for c in insp.get_columns("patient_allergies")}

    has_is_nkda = "is_nkda" in allergy_cols
    has_allergy_name = "allergy_name" in allergy_cols
    has_allergy_updated = "updated_at" in allergy_cols

    # -------------------------
    # Build SQL fragments based on availability
    # -------------------------

    # Admitted logic: for your hospice workflow, admitted patients are ACTIVE.
    # If patients.status doesn't exist, treat admitted as TRUE (view still works).
    admitted_expr = "TRUE"
    patient_status_select = "NULL::text AS patient_status"
    if has_patient_status:
        admitted_expr = "(p.status = 'ACTIVE')"
        patient_status_select = "p.status AS patient_status"

    mrn_select = "NULL::text AS mrn"
    if has_patient_mrn:
        mrn_select = "p.mrn AS mrn"

    last_select = "NULL::text AS last_name"
    if has_patient_last:
        last_select = "p.last_name AS last_name"

    first_select = "NULL::text AS first_name"
    if has_patient_first:
        first_select = "p.first_name AS first_name"

    dob_select = "NULL::date AS date_of_birth"
    age_select = "NULL::int AS age"
    if has_patient_dob:
        dob_select = "p.date_of_birth AS date_of_birth"
        age_select = "DATE_PART('year', AGE(CURRENT_DATE, p.date_of_birth))::int AS age"

    dx_updated_by_select = "NULL::uuid AS primary_dx_updated_by_id"
    if documented_by_col:
        dx_updated_by_select = f"rn_primary.{documented_by_col} AS primary_dx_updated_by_id"

    # Allergy aggregation
    # If table missing, we still return allergy_state='UNKNOWN' so UI can show "Not documented".
    allergy_state_expr = "'UNKNOWN'::text AS allergy_state"
    allergy_list_expr = "NULL::text AS allergy_list"
    allergy_last_updated_expr = "NULL::timestamp AS allergy_last_updated"

    if has_allergies and has_allergy_name:
        # If is_nkda exists we can safely compute NKDA vs HAS_ALLERGY vs NOT_DOCUMENTED
        if has_is_nkda:
            allergy_state_expr = """
            CASE
              WHEN COALESCE(MAX(pa.is_nkda), false) = true THEN 'NKDA'
              WHEN COUNT(pa.allergy_name) FILTER (WHERE pa.allergy_name IS NOT NULL AND pa.allergy_name <> '') > 0 THEN 'HAS_ALLERGY'
              ELSE 'NOT_DOCUMENTED'
            END AS allergy_state
            """
        else:
            # No NKDA column; infer from presence/absence
            allergy_state_expr = """
            CASE
              WHEN COUNT(pa.allergy_name) FILTER (WHERE pa.allergy_name IS NOT NULL AND pa.allergy_name <> '') > 0 THEN 'HAS_ALLERGY'
              ELSE 'NOT_DOCUMENTED'
            END AS allergy_state
            """

        allergy_list_expr = """
        STRING_AGG(pa.allergy_name, ', ' ORDER BY pa.allergy_name)
          FILTER (WHERE pa.allergy_name IS NOT NULL AND pa.allergy_name <> '') AS allergy_list
        """

        if has_allergy_updated:
            allergy_last_updated_expr = "MAX(pa.updated_at) AS allergy_last_updated"

    # Discrepancy hook (latest discrepancy row, shows OPEN/ACK/RES)
    disc_join = ""
    disc_fields = """
      NULL::uuid AS dx_discrepancy_id,
      NULL::text AS dx_discrepancy_status,
      false AS dx_discrepancy_open
    """
    if has_dx_disc:
        disc_join = """
        LEFT JOIN LATERAL (
          SELECT d.id, d.status, d.created_at
          FROM diagnosis_discrepancies d
          WHERE d.patient_id = p.id
          ORDER BY d.created_at DESC
          LIMIT 1
        ) disc ON true
        """
        disc_fields = """
          disc.id AS dx_discrepancy_id,
          disc.status AS dx_discrepancy_status,
          (disc.status = 'OPEN') AS dx_discrepancy_open
        """

    # -------------------------
    # Create or replace the face sheet view
    # -------------------------
    # RN-FIRST primary dx for admitted patients; provisional (referral) for non-admits.
    # Always returns both RN and CTI primary dx for audit drilldown.
    view_sql = f"""
    CREATE OR REPLACE VIEW patient_face_sheet_view AS
    SELECT
      p.id AS patient_id,
      {mrn_select},
      {last_select},
      {first_select},
      {dob_select},
      {age_select},
      {patient_status_select},
      {admitted_expr} AS is_admitted,

      -- Primary Dx selection logic:
      -- If admitted: prefer RN_IA primary, else show referral primary (provisional).
      CASE
        WHEN {admitted_expr} THEN COALESCE(rn_primary.description, referral_primary.description)
        ELSE referral_primary.description
      END AS primary_dx_description,

      CASE
        WHEN {admitted_expr} THEN COALESCE(rn_primary.icd_code, referral_primary.icd_code)
        ELSE referral_primary.icd_code
      END AS primary_dx_icd,

      CASE
        WHEN {admitted_expr} AND rn_primary.description IS NOT NULL THEN 'RN_IA'
        WHEN referral_primary.description IS NOT NULL THEN 'REFERRAL'
        ELSE NULL
      END AS primary_dx_source,

      -- Timestamp + who updated (RN side)
      rn_primary.documented_at AS primary_dx_updated_at,
      {dx_updated_by_select},

      -- RN related/secondary lists (admitted chart view)
      STRING_AGG(DISTINCT rn_other.description, ', ' ORDER BY rn_other.description)
        FILTER (WHERE rn_other.dx_type = 'RELATED' AND rn_other.description IS NOT NULL) AS related_dx_list,

      STRING_AGG(DISTINCT rn_other.description, ', ' ORDER BY rn_other.description)
        FILTER (WHERE rn_other.dx_type = 'SECONDARY' AND rn_other.description IS NOT NULL) AS secondary_dx_list,

      -- CTI and Referral primary dx always visible to drive reconciliation UI
      referral_primary.description AS referral_primary_dx_description,
      referral_primary.icd_code AS referral_primary_dx_icd,

      cti_primary.description AS cti_primary_dx_description,
      cti_primary.icd_code AS cti_primary_dx_icd,

      -- Allergy prominence hooks
      {allergy_state_expr},
      {allergy_list_expr},
      {allergy_last_updated_expr},

      -- Discrepancy hooks (tasking/NOE readiness)
      {disc_fields}

    FROM patients p

    -- RN primary
    LEFT JOIN diagnosis_sources rn_primary
      ON rn_primary.patient_id = p.id
     AND rn_primary.source = 'RN_IA'
     AND rn_primary.dx_type = 'PRIMARY'
     AND rn_primary.is_active = true

    -- RN related/secondary
    LEFT JOIN diagnosis_sources rn_other
      ON rn_other.patient_id = p.id
     AND rn_other.source = 'RN_IA'
     AND rn_other.dx_type IN ('RELATED','SECONDARY')
     AND rn_other.is_active = true

    -- Referral primary (provisional)
    LEFT JOIN diagnosis_sources referral_primary
      ON referral_primary.patient_id = p.id
     AND referral_primary.source = 'REFERRAL'
     AND referral_primary.dx_type = 'PRIMARY'
     AND referral_primary.is_active = true

    -- CTI primary
    LEFT JOIN diagnosis_sources cti_primary
      ON cti_primary.patient_id = p.id
     AND cti_primary.source = 'CTI'
     AND cti_primary.dx_type = 'PRIMARY'
     AND cti_primary.is_active = true

    {"LEFT JOIN patient_allergies pa ON pa.patient_id = p.id" if has_allergies else ""}

    {disc_join}

    GROUP BY
      p.id,
      {("p.mrn," if has_patient_mrn else "")}
      {("p.last_name," if has_patient_last else "")}
      {("p.first_name," if has_patient_first else "")}
      {("p.date_of_birth," if has_patient_dob else "")}
      {("p.status," if has_patient_status else "")}
      rn_primary.description,
      rn_primary.icd_code,
      rn_primary.documented_at,
      {("rn_primary."+documented_by_col+"," if documented_by_col else "")}
      referral_primary.description,
      referral_primary.icd_code,
      cti_primary.description,
      cti_primary.icd_code
      {(", disc.id, disc.status, disc.created_at" if has_dx_disc else "")}
    ;
    """

    # Execute view creation
    op.execute(text(view_sql))


def downgrade():
    op.execute("DROP VIEW IF EXISTS patient_face_sheet_view;")