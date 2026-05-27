# app/services/dx_policy.py

from __future__ import annotations

from typing import Tuple, Optional
from uuid import UUID

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session


def _resolve_policy_table(db: Session) -> Optional[str]:
    """
    Supports schema variants:
      - dx_primary_policy
      - dx_primary_policies
    """
    insp = inspect(db.get_bind())
    if insp.has_table("dx_primary_policy"):
        return "dx_primary_policy"
    if insp.has_table("dx_primary_policies"):
        return "dx_primary_policies"
    return None


def _resolve_reason_column(db: Session, table_name: str) -> Optional[str]:
    """
    Supports schema variants:
      - reason
      - rationale
    """
    insp = inspect(db.get_bind())
    cols = {c["name"] for c in insp.get_columns(table_name)}
    if "reason" in cols:
        return "reason"
    if "rationale" in cols:
        return "rationale"
    return None


def evaluate_primary_dx_policy(
    *,
    db: Session,
    tenant_id: UUID,
    icd10_code: str,
) -> Tuple[bool, Optional[str]]:
    """
    AUTHORITATIVE primary diagnosis policy evaluation.

    Baseline CMS/LCD hard rules (always enforced):
    - F* codes (mental/behavioral) cannot be primary hospice diagnosis
    - R* codes (symptoms/signs) cannot be primary hospice diagnosis
    - Z* codes (factors influencing health status) cannot be primary hospice diagnosis

    Then applies tenant-specific DB policy rules (dx_primary_policy / dx_primary_policies)
    as an overlay for additional restrictions.
    """

    if not db:
        raise RuntimeError("Database session is required for primary dx enforcement")

    if not tenant_id:
        raise RuntimeError("tenant_id is required for primary dx enforcement")

    # Empty ICD is allowed during draft/intake
    if not icd10_code:
        return True, None

    normalized_icd = icd10_code.strip().upper()
    if not normalized_icd:
        return True, None

    # ---------------------------------------------------------
    # ✅ Baseline hard blocks (CMS/LCD-aligned)
    # ---------------------------------------------------------
    if normalized_icd.startswith("F"):
        return False, "F-codes are not allowed as a primary hospice diagnosis"
    if normalized_icd.startswith("R"):
        return False, "R-codes are not allowed as a primary hospice diagnosis"
    if normalized_icd.startswith("Z"):
        return False, "Z-codes are not allowed as a primary hospice diagnosis"

    # ---------------------------------------------------------
    # DB policy overlay (additional tenant-specific blocks)
    # ---------------------------------------------------------
    table_name = _resolve_policy_table(db)
    if not table_name:
        # No table => baseline only
        return True, None

    reason_col = _resolve_reason_column(db, table_name)

    insp = inspect(db.get_bind())
    cols = {c["name"] for c in insp.get_columns(table_name)}
    required = {"tenant_id", "allow_primary", "code_pattern"}
    if not required.issubset(cols):
        return True, None

    # If reason column exists, return reason string when blocked
    if reason_col:
        sql = text(
            f"""
            SELECT {reason_col}
            FROM {table_name}
            WHERE tenant_id = :tenant_id
              AND allow_primary = false
              AND :code LIKE code_pattern
            LIMIT 1
            """
        )
        reason = db.execute(
            sql,
            {"tenant_id": str(tenant_id), "code": normalized_icd},
        ).scalar()

        if reason:
            return False, str(reason)
        return True, None

    # No reason column — still enforce block, but return None reason
    sql = text(
        f"""
        SELECT 1
        FROM {table_name}
        WHERE tenant_id = :tenant_id
          AND allow_primary = false
          AND :code LIKE code_pattern
        LIMIT 1
        """
    )
    blocked = db.execute(
        sql,
        {"tenant_id": str(tenant_id), "code": normalized_icd},
    ).scalar()

    if blocked:
        return False, None

    return True, None


def is_primary_allowed(
    db: Session,
    *,
    tenant_id: UUID,
    code: str,
    **kwargs,
) -> Tuple[bool, Optional[str]]:
    """
    BACKWARD-COMPATIBILITY wrapper required by app/api/patients.py

    Usage:
      allowed, reason = is_primary_allowed(db, tenant_id=..., code="I50.9")

    Returns:
      (allowed, reason)
    """
    return evaluate_primary_dx_policy(
        db=db,
        tenant_id=tenant_id,
        icd10_code=code,
    )