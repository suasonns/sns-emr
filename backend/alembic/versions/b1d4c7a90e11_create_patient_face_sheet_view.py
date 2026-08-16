"""create patient_face_sheet_view

Admission gating and NOE readiness query this view, which existed only in the
hand-built development database. It derives from the tables that already own
the data - patients, patient_facesheet and assessment_discrepancies - so it
introduces no second source of truth.

Revision ID: b1d4c7a90e11
Revises: 521d501c6eea
Create Date: 2026-08-15
"""

from typing import Sequence, Union

from alembic import op

revision: str = "b1d4c7a90e11"
down_revision: Union[str, Sequence[str], None] = "521d501c6eea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


VIEW_SQL = """
CREATE OR REPLACE VIEW patient_face_sheet_view AS
SELECT
    p.id                AS patient_id,
    p.tenant_id         AS tenant_id,
    p.mrn               AS mrn,
    p.status            AS patient_status,
    p.admission_status  AS admission_status,
    CASE
        WHEN fs.has_allergies IS TRUE
             AND NULLIF(BTRIM(COALESCE(fs.allergies, '')), '') IS NOT NULL
            THEN 'DOCUMENTED'
        WHEN fs.has_allergies IS FALSE
            THEN 'NKDA'
        ELSE 'NOT_DOCUMENTED'
    END                 AS allergy_state,
    EXISTS (
        SELECT 1
        FROM assessment_discrepancies d
        WHERE d.patient_id = p.id
          AND d.resolved IS NOT TRUE
          AND UPPER(COALESCE(d.domain, '')) LIKE '%DIAGNOS%'
    )                   AS dx_discrepancy_open
FROM patients p
LEFT JOIN patient_facesheet fs
       ON fs.patient_id = p.id
      AND fs.deleted_at IS NULL
WHERE p.deleted_at IS NULL
"""


def upgrade() -> None:
    op.execute(VIEW_SQL)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS patient_face_sheet_view")
