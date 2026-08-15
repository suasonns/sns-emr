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