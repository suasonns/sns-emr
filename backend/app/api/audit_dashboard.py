from __future__ import annotations

from typing import Generator, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal


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
# TENANT RESOLUTION
# =========================================================

def _resolve_tenant_id(
    request: Request,
    db: Session,
    tenant_id: Optional[UUID],
) -> UUID:
    """
    Resolve tenant_id from:
    1) explicit query param
    2) request.state.tenant_id
    3) db.info["tenant_id"]
    4) first known patient tenant (dev fallback)
    """
    if tenant_id:
        return tenant_id

    if hasattr(request.state, "tenant_id") and request.state.tenant_id:
        return request.state.tenant_id

    if "tenant_id" in db.info and db.info["tenant_id"]:
        return db.info["tenant_id"]

    row = db.execute(
        text(
            """
            SELECT tenant_id
            FROM patients
            ORDER BY created_at ASC
            LIMIT 1
            """
        )
    ).fetchone()

    if not row:
        raise HTTPException(status_code=500, detail="Unable to resolve tenant_id")

    return row[0]


# =========================================================
# OVERVIEW DASHBOARD
# =========================================================

@router.get("/overview")
def get_audit_dashboard_overview(
    request: Request,
    tenant_id: Optional[UUID] = Query(
        None,
        description="Optional explicit tenant_id override",
    ),
    days: int = Query(
        30,
        ge=1,
        le=365,
        description="Rolling audit window in days",
    ),
    db: Session = Depends(get_db),
):
    resolved_tenant_id = _resolve_tenant_id(request, db, tenant_id)

    # -----------------------------------------------------
    # SUMMARY COUNTS
    # -----------------------------------------------------
    summary_row = db.execute(
        text(
            """
            WITH refusal_counts AS (
                SELECT
                    COUNT(*)::int AS total_refusals,
                    COUNT(*) FILTER (WHERE discipline IN ('RN', 'MD', 'F2F'))::int AS mandatory_service_visit_refusals,
                    COUNT(*) FILTER (WHERE discipline IN ('SW', 'CHAPLAIN', 'AIDE', 'LVN'))::int AS reoffer_service_refusals
                FROM refusals
                WHERE tenant_id = :tenant_id
                  AND refused_at >= NOW() - (:days || ' days')::interval
            ),
            task_counts AS (
                SELECT
                    COUNT(*) FILTER (
                        WHERE task_type IN ('MSW_REOFFER', 'CHAPLAIN_REOFFER', 'AIDE_REOFFER')
                          AND status = 'PENDING'
                    )::int AS pending_reoffer_tasks,

                    COUNT(*) FILTER (
                        WHERE task_type = 'OTHER'
                          AND status = 'PENDING'
                          AND alert_reason IN (
                              'RN_VISIT_REFUSED_RESCHEDULE_REQUIRED',
                              'MD_VISIT_REFUSED_RESCHEDULE_REQUIRED',
                              'F2F_VISIT_REFUSED_RESCHEDULE_REQUIRED'
                          )
                    )::int AS pending_staff_reminder_tasks
                FROM tasks
                WHERE tenant_id = :tenant_id
                  AND created_at >= NOW() - (:days || ' days')::interval
            ),
            visit_counts AS (
                SELECT
                    COUNT(*) FILTER (WHERE UPPER(status) = 'FINALIZED')::int AS finalized_visits,
                    COUNT(*) FILTER (WHERE UPPER(status) = 'MISSED')::int AS missed_visits,
                    COUNT(*) FILTER (WHERE UPPER(status) = 'RESCHEDULED')::int AS rescheduled_visits
                FROM visits
                WHERE tenant_id = :tenant_id
                  AND COALESCE(updated_at, created_at) >= NOW() - (:days || ' days')::interval
            )
            SELECT
                refusal_counts.total_refusals,
                refusal_counts.mandatory_service_visit_refusals,
                refusal_counts.reoffer_service_refusals,
                task_counts.pending_reoffer_tasks,
                task_counts.pending_staff_reminder_tasks,
                visit_counts.finalized_visits,
                visit_counts.missed_visits,
                visit_counts.rescheduled_visits
            FROM refusal_counts, task_counts, visit_counts
            """
        ),
        {"tenant_id": resolved_tenant_id, "days": days},
    ).mappings().one()

    # -----------------------------------------------------
    # DISCIPLINE BREAKDOWN
    # -----------------------------------------------------
    discipline_rows = db.execute(
        text(
            """
            SELECT
                discipline,
                COUNT(*)::int AS refusal_count
            FROM refusals
            WHERE tenant_id = :tenant_id
              AND refused_at >= NOW() - (:days || ' days')::interval
            GROUP BY discipline
            ORDER BY refusal_count DESC, discipline ASC
            """
        ),
        {"tenant_id": resolved_tenant_id, "days": days},
    ).mappings().all()

    # -----------------------------------------------------
    # TASK BREAKDOWN
    # -----------------------------------------------------
    task_rows = db.execute(
        text(
            """
            SELECT
                task_type::text AS task_type,
                status::text AS status,
                COUNT(*)::int AS task_count
            FROM tasks
            WHERE tenant_id = :tenant_id
              AND created_at >= NOW() - (:days || ' days')::interval
              AND (
                    task_type IN ('MSW_REOFFER', 'CHAPLAIN_REOFFER', 'AIDE_REOFFER')
                    OR (
                        task_type = 'OTHER'
                        AND alert_reason IN (
                            'RN_VISIT_REFUSED_RESCHEDULE_REQUIRED',
                            'MD_VISIT_REFUSED_RESCHEDULE_REQUIRED',
                            'F2F_VISIT_REFUSED_RESCHEDULE_REQUIRED'
                        )
                    )
                  )
            GROUP BY task_type, status
            ORDER BY task_type, status
            """
        ),
        {"tenant_id": resolved_tenant_id, "days": days},
    ).mappings().all()

    return {
        "tenant_id": str(resolved_tenant_id),
        "window_days": days,
        "summary": {
            "total_refusals": summary_row["total_refusals"],
            "mandatory_service_visit_refusals": summary_row["mandatory_service_visit_refusals"],
            "reoffer_service_refusals": summary_row["reoffer_service_refusals"],
            "pending_reoffer_tasks": summary_row["pending_reoffer_tasks"],
            "pending_staff_reminder_tasks": summary_row["pending_staff_reminder_tasks"],
            "finalized_visits": summary_row["finalized_visits"],
            "missed_visits": summary_row["missed_visits"],
            "rescheduled_visits": summary_row["rescheduled_visits"],
        },
        "by_discipline": [dict(row) for row in discipline_rows],
        "task_breakdown": [dict(row) for row in task_rows],
    }


# =========================================================
# PATIENT RISK LIST
# =========================================================

@router.get("/patients")
def get_audit_dashboard_patients(
    request: Request,
    tenant_id: Optional[UUID] = Query(
        None,
        description="Optional explicit tenant_id override",
    ),
    days: int = Query(
        30,
        ge=1,
        le=365,
        description="Rolling audit window in days",
    ),
    limit: int = Query(
        50,
        ge=1,
        le=500,
        description="Maximum number of patient rows to return",
    ),
    db: Session = Depends(get_db),
):
    resolved_tenant_id = _resolve_tenant_id(request, db, tenant_id)

    rows = db.execute(
        text(
            """
            WITH refusal_agg AS (
                SELECT
                    r.patient_id,
                    COUNT(*)::int AS total_refusals,
                    COUNT(*) FILTER (WHERE r.discipline IN ('RN', 'MD', 'F2F'))::int AS mandatory_service_visit_refusals,
                    COUNT(*) FILTER (WHERE r.discipline IN ('SW', 'CHAPLAIN', 'AIDE', 'LVN'))::int AS reoffer_service_refusals,
                    MAX(r.refused_at) AS latest_refusal_at
                FROM refusals r
                WHERE r.tenant_id = :tenant_id
                  AND r.refused_at >= NOW() - (:days || ' days')::interval
                GROUP BY r.patient_id
            ),
            pending_task_agg AS (
                SELECT
                    t.patient_id,
                    COUNT(*) FILTER (
                        WHERE t.task_type IN ('MSW_REOFFER', 'CHAPLAIN_REOFFER', 'AIDE_REOFFER')
                          AND t.status = 'PENDING'
                    )::int AS pending_reoffer_tasks,
                    COUNT(*) FILTER (
                        WHERE t.task_type = 'OTHER'
                          AND t.status = 'PENDING'
                          AND t.alert_reason IN (
                              'RN_VISIT_REFUSED_RESCHEDULE_REQUIRED',
                              'MD_VISIT_REFUSED_RESCHEDULE_REQUIRED',
                              'F2F_VISIT_REFUSED_RESCHEDULE_REQUIRED'
                          )
                    )::int AS pending_staff_reminder_tasks
                FROM tasks t
                WHERE t.tenant_id = :tenant_id
                  AND t.created_at >= NOW() - (:days || ' days')::interval
                GROUP BY t.patient_id
            ),
            visit_agg AS (
                SELECT
                    v.patient_id,
                    COUNT(*) FILTER (WHERE UPPER(v.status) = 'MISSED')::int AS missed_visits,
                    COUNT(*) FILTER (WHERE UPPER(v.status) = 'RESCHEDULED')::int AS rescheduled_visits,
                    COUNT(*) FILTER (WHERE UPPER(v.status) = 'FINALIZED')::int AS finalized_visits
                FROM visits v
                WHERE v.tenant_id = :tenant_id
                  AND COALESCE(v.updated_at, v.created_at) >= NOW() - (:days || ' days')::interval
                GROUP BY v.patient_id
            )
            SELECT
                p.id::text AS patient_id,
                p.mrn,
                p.full_name,
                COALESCE(r.total_refusals, 0) AS total_refusals,
                COALESCE(r.mandatory_service_visit_refusals, 0) AS mandatory_service_visit_refusals,
                COALESCE(r.reoffer_service_refusals, 0) AS reoffer_service_refusals,
                COALESCE(t.pending_reoffer_tasks, 0) AS pending_reoffer_tasks,
                COALESCE(t.pending_staff_reminder_tasks, 0) AS pending_staff_reminder_tasks,
                COALESCE(v.missed_visits, 0) AS missed_visits,
                COALESCE(v.rescheduled_visits, 0) AS rescheduled_visits,
                COALESCE(v.finalized_visits, 0) AS finalized_visits,
                r.latest_refusal_at
            FROM patients p
            LEFT JOIN refusal_agg r ON r.patient_id = p.id
            LEFT JOIN pending_task_agg t ON t.patient_id = p.id
            LEFT JOIN visit_agg v ON v.patient_id = p.id
            WHERE p.tenant_id = :tenant_id
              AND (
                    COALESCE(r.total_refusals, 0) > 0
                    OR COALESCE(t.pending_reoffer_tasks, 0) > 0
                    OR COALESCE(t.pending_staff_reminder_tasks, 0) > 0
                    OR COALESCE(v.missed_visits, 0) > 0
                    OR COALESCE(v.rescheduled_visits, 0) > 0
                  )
            ORDER BY
                COALESCE(t.pending_staff_reminder_tasks, 0) DESC,
                COALESCE(t.pending_reoffer_tasks, 0) DESC,
                COALESCE(r.total_refusals, 0) DESC,
                r.latest_refusal_at DESC NULLS LAST
            LIMIT :limit
            """
        ),
        {"tenant_id": resolved_tenant_id, "days": days, "limit": limit},
    ).mappings().all()

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
):
    resolved_tenant_id = _resolve_tenant_id(request, db, tenant_id)

    rows = db.execute(
        text(
            """
            WITH latest_visit AS (
                SELECT DISTINCT ON (v.patient_id)
                    v.patient_id,
                    v.visit_datetime AS last_visit_at,
                    u.full_name AS attending_physician
                FROM visits v
                LEFT JOIN users u ON u.id = v.provider_id
                WHERE v.tenant_id = :tenant_id
                ORDER BY v.patient_id, v.visit_datetime DESC, v.updated_at DESC
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
                p.full_name,
                p.date_of_birth,
                p.primary_diagnosis,
                p.status AS patient_status,
                p.admission_status,
                COALESCE(p.on_service_at, p.soc_date, p.hospice_election_date::timestamp) AS admission_at,
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
            LEFT JOIN latest_visit lv ON lv.patient_id = p.id
            LEFT JOIN primary_payer pp ON pp.patient_id = p.id::text
            WHERE p.tenant_id = :tenant_id
            ORDER BY p.full_name ASC
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