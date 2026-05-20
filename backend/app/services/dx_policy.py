# app/services/dx_policy.py

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import text


def is_primary_allowed(
    db: Optional[Session],
    *,
    tenant_id: Optional[str] = None,
    diagnosis_text: Optional[str] = None,
    diagnosis_icd10: Optional[str] = None,
) -> bool:
    """
    Primary Dx Governance (Policy Gate)

    Purpose:
      - Returns True if the selected primary diagnosis is not on a CMS/agency prohibited list.
      - Returns False only for explicit policy-prohibited diagnoses (objective rule).
      - This function does NOT make hospice eligibility decisions; it enforces a coding policy list.

    Enterprise behavior:
      - Fail-open if dependencies are missing (do not crash the application).
      - If db is unavailable, return True to avoid blocking workflows due to infrastructure issues.

    NOTE:
      - If you want stricter enforcement later, do that in the API layer with explicit messaging,
        not by raising exceptions here.
    """

    # If we cannot evaluate safely, do not block system operation.
    if db is None:
        return True

    icd = (diagnosis_icd10 or "").strip().upper()
    dx_text = (diagnosis_text or "").strip().lower()

    # If nothing provided, allow.
    if not icd and not dx_text:
        return True

    try:
        # 1) Check prohibited primary ICD10 list (preferred)
        # Table: cms_prohibited_primary_dx
        # Columns often: icd10_code, is_active, tenant_id (optional)
        q = """
        SELECT 1
        FROM cms_prohibited_primary_dx
        WHERE is_active = true
          AND (
                (:icd <> '' AND upper(icd10_code) = :icd)
                OR (:dx_text <> '' AND lower(dx_text) = :dx_text)
              )
        """
        params = {"icd": icd, "dx_text": dx_text}
        # If tenant scoping exists, apply it safely (no failure if column absent).
        if tenant_id:
            q = q + " AND (tenant_id::text = :tenant_id OR tenant_id IS NULL)"
            params["tenant_id"] = str(tenant_id)

        hit = db.execute(text(q), params).scalar()
        if hit:
            return False

    except Exception:
        # Do not crash application startup if table/column is absent in this environment.
        return True

    return True