from __future__ import annotations

from typing import Generator, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.permissions import require_roles
from app.core.security import CurrentUser
from app.services.audit_logger import log_event


router = APIRouter(prefix="/audit-dashboard", tags=["audit-dashboard"])


# =========================================================
# DB DEPENDENCY
# =========================================================

def get_db(request: Request) -> Generator[Session, None, None]:
    db = SessionLocal()
    request.state.db = db
    try:
        yield db
    finally:
        db.close()


# =========================================================
# TENANT RESOLUTION (STRICT)
# =========================================================

def _resolve_tenant_id(
    request: Request,
    db: Session,
    tenant_id: Optional[UUID],
    user: CurrentUser,
) -> UUID:

    if tenant_id:
        resolved = tenant_id
    elif hasattr(request.state, "tenant_id") and request.state.tenant_id:
        resolved = request.state.tenant_id
    elif "tenant_id" in db.info and db.info["tenant_id"]:
        resolved = db.info["tenant_id"]
    elif user.tenant_id:
        resolved = user.tenant_id
    else:
        raise HTTPException(400, "tenant_id is required")

    # ✅ enforce tenant isolation
    if user.tenant_id != resolved:
        raise HTTPException(403, "Tenant mismatch")

    return resolved


# =========================================================
# PATIENT RISK LIST (PRODUCTION SAFE)
# =========================================================

@router.get("/patients")
def get_audit_dashboard_patients(
    request: Request,
    tenant_id: Optional[UUID] = Query(None),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["ADMIN", "DPCS", "QA"])),
):

    resolved_tenant_id = _resolve_tenant_id(request, db, tenant_id, user)

    rows = db.execute(
        text(
            """
            WITH refusal_agg AS (
                SELECT
                    r.patient_id,
                    COUNT(*)::int AS total_refusals,
                    MAX(r.refused_at) AS latest_refusal_at
                FROM refusals r
                WHERE r.tenant_id = :tenant_id
                  AND r.refused_at >= NOW() - (:days || ' days')::interval
                GROUP BY r.patient_id
            ),
            visit_agg AS (
                SELECT
                    v.patient_id,
                    COUNT(*) FILTER (WHERE UPPER(v.status) = 'MISSED')::int AS missed_visits,
                    COUNT(*) FILTER (WHERE UPPER(v.status) = 'RESCHEDULED')::int AS rescheduled_visits
                FROM visits v
                WHERE v.tenant_id = :tenant_id
                  AND COALESCE(v.updated_at, v.created_at) >= NOW() - (:days || ' days')::interval
                GROUP BY v.patient_id
            )
            SELECT
                p.id::text AS patient_id,
                p.mrn,

                -- ✅ CORRECT IDENTITY SOURCE
                COALESCE(
                    TRIM(CONCAT_WS(
                        ' ',
                        fs.first_name,
                        fs.middle_name,
                        fs.last_name
                    )),
                    'UNKNOWN PATIENT'
                ) AS patient_name,

                COALESCE(r.total_refusals, 0) AS total_refusals,
                COALESCE(v.missed_visits, 0) AS missed_visits,
                COALESCE(v.rescheduled_visits, 0) AS rescheduled_visits,
                r.latest_refusal_at

            FROM patients p
            LEFT JOIN patient_facesheet fs ON fs.patient_id = p.id
            LEFT JOIN refusal_agg r ON r.patient_id = p.id
            LEFT JOIN visit_agg v ON v.patient_id = p.id

            WHERE p.tenant_id = :tenant_id
              AND (
                    COALESCE(r.total_refusals, 0) > 0
                    OR COALESCE(v.missed_visits, 0) > 0
                    OR COALESCE(v.rescheduled_visits, 0) > 0
                  )

            ORDER BY r.total_refusals DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        {
            "tenant_id": resolved_tenant_id,
            "days": days,
            "limit": limit,
            "offset": offset,
        },
    ).mappings().all()

    # ✅ AUDIT ACCESS
    log_event(
        user_id=user.user_id,
        role=user.role,
        action="VIEW_AUDIT_DASHBOARD",
        entity_type="audit_dashboard",
        metadata={
            "tenant_id": str(resolved_tenant_id),
            "days": days,
        },
    )

    return {
        "tenant_id": str(resolved_tenant_id),
        "window_days": days,
        "patient_count": len(rows),
        "patients": [dict(row) for row in rows],
    }


# =========================================================
# CENSUS WORKSPACE
# =========================================================

@router.get("/census")
def get_audit_dashboard_census(
    request: Request,
    tenant_id: Optional[UUID] = Query(
        None,
        description="Optional explicit tenant_id override",
    ),
    limit: int = Query(
        500,
        ge=1,
        le=1000,
        description="Maximum number of patient rows to return",
    ),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(["ADMIN", "DPCS", "QA"])),
):
    resolved_tenant_id = _resolve_tenant_id(request, db, tenant_id, user)

    rows = db.execute(
        text(
            """
            WITH latest_visit AS (
                SELECT DISTINCT ON (v.patient_id)
                    v.patient_id,
                    v.visit_datetime AS last_visit_at,
                    COALESCE(
                        NULLIF(TRIM(CONCAT_WS(' ', u.first_name, u.middle_name, u.last_name)), ''),
                        u.email,
                        '—'
                    ) AS attending_physician
                FROM visits v
                LEFT JOIN users u ON u.id = v.provider_id
                WHERE v.tenant_id = :tenant_id
                ORDER BY v.patient_id, v.visit_datetime DESC, v.updated_at DESC
            ),
            latest_admission AS (
                SELECT DISTINCT ON (a.patient_id)
                    a.patient_id,
                    COALESCE(a.soc_date, a.admission_date) AS admission_at
                FROM admissions a
                WHERE a.tenant_id = :tenant_id
                ORDER BY a.patient_id, a.created_at DESC
            ),
            primary_payer AS (
                SELECT DISTINCT ON (pp.patient_id)
                    pp.patient_id,
                    pp.payer_name
                FROM patient_payers pp
                ORDER BY
                    pp.patient_id,
                    COALESCE(pp.is_primary, false) DESC,
                    COALESCE(pp.updated_at, pp.created_at) DESC NULLS LAST,
                    pp.id
            )
            SELECT
                p.id::text AS patient_id,
                p.mrn,
                COALESCE(
                    NULLIF(TRIM(CONCAT_WS(' ', fs.first_name, fs.middle_name, fs.last_name)), ''),
                    p.mrn
                ) AS full_name,
                p.date_of_birth,
                p.primary_diagnosis,
                p.status AS patient_status,
                p.admission_status,
                COALESCE(la.admission_at, p.hospice_election_date::timestamp) AS admission_at,
                p.discharge_date,
                p.discharge_reason,
                COALESCE(lv.attending_physician, '—') AS attending_physician,
                COALESCE(pp.payer_name, '—') AS payer_name,
                lv.last_visit_at,
                CASE
                    WHEN p.status = 'DECEASED' OR p.admission_status = 'DECEASED' THEN 'Deceased'
                    WHEN p.status = 'DISCHARGED' OR p.admission_status = 'DISCHARGED' OR p.discharge_date IS NOT NULL THEN 'Discharged'
                    WHEN p.status = 'REVOKED' OR p.admission_status = 'REVOKED' OR p.not_admitted_at IS NOT NULL THEN 'Revoked'
                    ELSE 'Active'
                END AS census_bucket
            FROM patients p
            LEFT JOIN patient_facesheet fs ON fs.patient_id = p.id AND fs.tenant_id = p.tenant_id
            LEFT JOIN latest_visit lv ON lv.patient_id = p.id
            LEFT JOIN latest_admission la ON la.patient_id = p.id
            LEFT JOIN primary_payer pp ON pp.patient_id = p.id
            WHERE p.tenant_id = :tenant_id
            ORDER BY full_name ASC
            LIMIT :limit
            """
        ),
        {"tenant_id": resolved_tenant_id, "limit": limit},
    ).mappings().all()

    return {
        "tenant_id": str(resolved_tenant_id),
        "patient_count": len(rows),
        "patients": [dict(row) for row in rows],
    }
