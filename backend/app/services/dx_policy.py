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
    # If neither exists, we still can block/allow, but we cannot return a reason string
    return None


def evaluate_primary_dx_policy(
    *,
    db: Session,
    tenant_id: UUID,
    icd10_code: str,
) -> Tuple[bool, Optional[str]]:
    """
    AUTHORITATIVE primary diagnosis policy evaluation.

    Returns:
      (True, None) if allowed as Primary Dx
      (False, reason) if prohibited as Primary Dx

    Schema-flexible and survey-safe.
    """

    if not db:
        raise RuntimeError("Database session is required for primary dx enforcement")

    if not tenant_id:
        raise RuntimeError("tenant_id is required for primary dx enforcement")

    if not icd10_code:
        return True, None

    normalized_icd = icd10_code.strip().upper()

    table_name = _resolve_policy_table(db)
    if not table_name:
        # If policy table isn't present, fail-open to keep system operational.
        # (If you prefer fail-closed, change this to return False with reason.)
        return True, None

    reason_col = _resolve_reason_column(db, table_name)

    # The policy table must have these columns to function:
    # tenant_id, allow_primary, code_pattern
    insp = inspect(db.get_bind())
    cols = {c["name"] for c in insp.get_columns(table_name)}
    required = {"tenant_id", "allow_primary", "code_pattern"}
    if not required.issubset(cols):
        return True, None

    # Build a safe SQL query that works regardless of ORM model shape
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
        reason = db.execute(sql, {"tenant_id": str(tenant_id), "code": normalized_icd}).scalar()
        if reason:
            return False, str(reason)
        return True, None

    # No reason column available — still enforce allow_primary, but reason is None
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
    blocked = db.execute(sql, {"tenant_id": str(tenant_id), "code": normalized_icd}).scalar()
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

    Supports:
      allowed, reason = is_primary_allowed(db, tenant_id=..., code="I50.9")

    Returns:
      (allowed, reason)
    """
    return evaluate_primary_dx_policy(db=db, tenant_id=tenant_id, icd10_code=code)