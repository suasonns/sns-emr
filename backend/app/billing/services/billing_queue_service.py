from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def get_billing_queue(
    db: Session,
    tenant_id: str | None = None,
    status: str | None = None,
    billing_cycle_id: str | None = None,
    q: str | None = None,
):
    """
    ✅ ENTERPRISE-SAFE BILLING QUEUE SERVICE

    Features:
    - Safe patient identity display fields
    - Non-breaking LEFT JOIN
    - Search by patient_id, full_name, MRN, DOB
    - Audit logging for billing queue access
    - Audit logging is NON-BLOCKING (billing queue still works if audit fails)
    """

    query = """
    SELECT
        bs.patient_id,

        -- SAFE DISPLAY FIELDS
        COALESCE(p.full_name, NULL) AS patient_name,
        COALESCE(p.mrn, NULL) AS patient_mrn,
        COALESCE(p.date_of_birth::text, NULL) AS patient_dob,

        -- TENANT INFO
        bs.tenant_id::text AS tenant_id,
        NULL::text AS tenant_name,

        -- BILLING CORE
        bs.billing_cycle_id,
        bs.status,
        bs.risk_score,
        bs.total_units

    FROM billing_summary bs

    LEFT JOIN patients p
        ON p.id = bs.patient_id

    WHERE 1=1
    """

    params: dict[str, str] = {}

    # ---------------------------------------------------------
    # FILTERS
    # ---------------------------------------------------------
    if tenant_id:
        query += " AND bs.tenant_id::text = :tenant_id"
        params["tenant_id"] = tenant_id

    if status:
        query += " AND bs.status = :status"
        params["status"] = status

    if billing_cycle_id:
        query += " AND bs.billing_cycle_id = :billing_cycle_id"
        params["billing_cycle_id"] = billing_cycle_id

    if q:
        query += """
        AND (
            bs.patient_id::text ILIKE :search
            OR p.full_name ILIKE :search
            OR p.mrn ILIKE :search
            OR p.date_of_birth::text LIKE :search
        )
        """
        params["search"] = f"%{q}%"

    query += " ORDER BY bs.created_at DESC"

    # ---------------------------------------------------------
    # RUN QUERY
    # ---------------------------------------------------------
    result = db.execute(text(query), params).mappings().all()
    rows = [dict(row) for row in result]

    # ---------------------------------------------------------
    # AUDIT LOGGING (NON-BLOCKING)
    # ---------------------------------------------------------
    # Important:
    # - AuditLog.tenant_id is required in your model
    # - Only log when tenant_id is available
    # - Never allow audit failure to break billing queue
    if tenant_id:
        try:
            audit_log = AuditLog(
                id=uuid4(),
                tenant_id=UUID(tenant_id),
                user_id=None,
                role=None,
                request_id=str(uuid4()),
                ip_address=None,
                action_type="BILLING_QUEUE_VIEW",
                entity_type="billing_queue",
                entity_id=None,
                description="User accessed billing queue",
                event_metadata={
                    "status_filter": status,
                    "billing_cycle_id": billing_cycle_id,
                    "search_query": q,
                    "result_count": len(rows),
                },
            )
            db.add(audit_log)
            db.commit()
        except Exception:
            db.rollback()

    return rows


def get_billing_tenants(db: Session):
    """
    ✅ SAFE VERSION
    Returns tenant IDs for billing filter dropdown.
    """

    query = """
    SELECT
        id::text AS tenant_id
    FROM tenants
    ORDER BY id
    """

    result = db.execute(text(query)).mappings().all()
    return [dict(row) for row in result]