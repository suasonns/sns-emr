"""recreate patient_face_sheet_view with ICD-only dx mismatch

Revision ID: 5a0226f4b90e
Revises: ccff1034bff9
Create Date: 2026-05-06 16:18:20.689263
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "5a0226f4b90e"
down_revision: Union[str, Sequence[str], None] = "ccff1034bff9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop existing view if it exists
    op.execute("DROP VIEW IF EXISTS public.patient_face_sheet_view;")

    # Recreate view with ICD-only discrepancy logic
    op.execute(
        """
        CREATE VIEW public.patient_face_sheet_view AS
        WITH rn_primary AS (
            SELECT
                patient_id,
                icd_code,
                description
            FROM diagnosis_sources
            WHERE source = 'RN_IA'
              AND dx_type = 'PRIMARY'
              AND is_active = true
        ),
        cti_primary AS (
            SELECT
                patient_id,
                icd_code,
                description
            FROM diagnosis_sources
            WHERE source = 'CTI'
              AND dx_type = 'PRIMARY'
              AND is_active = true
        )
        SELECT
            p.id AS patient_id,
            p.status AS patient_status,

            -- Primary diagnosis ICD (authoritative for admission / NOE)
            COALESCE(rn_primary.icd_code, cti_primary.icd_code) AS primary_dx_icd,

            -- HARD STOP: ICD-only mismatch
            CASE
                WHEN rn_primary.icd_code IS NOT NULL
                 AND cti_primary.icd_code IS NOT NULL
                 AND rn_primary.icd_code <> cti_primary.icd_code
                THEN true
                ELSE false
            END AS dx_discrepancy_open,

            -- Optional human-readable status
            CASE
                WHEN rn_primary.icd_code IS NOT NULL
                 AND cti_primary.icd_code IS NOT NULL
                 AND rn_primary.icd_code <> cti_primary.icd_code
                THEN 'OPEN'
                ELSE 'NONE'
            END AS dx_discrepancy_status,

            -- Allergy state (minimal but survey-safe)
            CASE
                WHEN ap.is_nkda = true THEN 'NKDA'
                WHEN pa.patient_id IS NOT NULL THEN 'HAS_ALLERGY'
                ELSE 'NOT_DOCUMENTED'
            END AS allergy_state

        FROM patients p
        LEFT JOIN rn_primary ON rn_primary.patient_id = p.id
        LEFT JOIN cti_primary ON cti_primary.patient_id = p.id
        LEFT JOIN patient_allergy_profiles ap ON ap.patient_id = p.id
        LEFT JOIN patient_allergies pa ON pa.patient_id = p.id;
        """
    )

    # Environment-safe OWNER + GRANTS:
    # - Always set owner to current_user (works locally + Azure)
    # - Always grant select to current_user
    # - If legacy role sns_user exists, grant select to it too
    op.execute(
        """
        DO $$
        BEGIN
          EXECUTE 'ALTER VIEW public.patient_face_sheet_view OWNER TO ' || quote_ident(current_user);
          EXECUTE 'GRANT SELECT ON public.patient_face_sheet_view TO ' || quote_ident(current_user);

          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sns_user') THEN
            EXECUTE 'GRANT SELECT ON public.patient_face_sheet_view TO sns_user';
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    # Forward-only system: do NOT attempt to restore old logic
    # We intentionally leave the view in place
    pass