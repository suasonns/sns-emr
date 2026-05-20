# app/services/benefit_periods.py

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_current_benefit_period(
    db: Session,
    *,
    patient_id: str,
    tenant_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Returns the current (active) Medicare benefit period for a patient, if present.

    Compliance intent:
      - Tasks/visits should be attributable to benefit periods when available.
      - If no benefit period exists, workflows must still function (returns None).

    Enterprise behavior:
      - Deterministic selection (most recent active period).
      - Tenant-safe when tenant_id is provided.
      - Does not mutate data.
    """

    if db is None:
        raise ValueError("db session is required")
    if not patient_id:
        raise ValueError("patient_id is required")

    # Try common patterns: ACTIVE/current flag, or date range containing today.
    # We keep this schema-tolerant and safe.
    params = {"patient_id": patient_id}
    tenant_clause = ""
    if tenant_id:
        tenant_clause = " AND tenant_id = :tenant_id"
        params["tenant_id"] = tenant_id

    # 1) Prefer explicit "is_current" or "status" if present.
    # If those columns don't exist in a given environment, we fall back.
    queries = [
        (
            f"""
            SELECT *
            FROM benefit_periods
            WHERE patient_id = :patient_id
              {tenant_clause}
              AND is_current = true
            ORDER BY start_date DESC NULLS LAST
            LIMIT 1
            """
        ),
        (
            f"""
            SELECT *
            FROM benefit_periods
            WHERE patient_id = :patient_id
              {tenant_clause}
              AND status = 'ACTIVE'
            ORDER BY start_date DESC NULLS LAST
            LIMIT 1
            """
        ),
        (
            f"""
            SELECT *
            FROM benefit_periods
            WHERE patient_id = :patient_id
              {tenant_clause}
              AND (start_date IS NULL OR start_date <= now())
              AND (end_date IS NULL OR end_date >= now())
            ORDER BY start_date DESC NULLS LAST
            LIMIT 1
            """
        ),
    ]

    for q in queries:
        try:
            row = db.execute(text(q), params).mappings().first()
            if row:
                return dict(row)
        except Exception:
            # Try next query style if columns don't exist
            continue

    return None