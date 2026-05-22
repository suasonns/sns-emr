# app/services/awareness_group.py

from __future__ import annotations

from typing import List, Dict
from sqlalchemy.orm import Session

from app.models.user import User


def resolve_clinical_awareness_group(
    db: Session,
    *,
    tenant_id,
    patient_id,
) -> List[Dict[str, str]]:
    """
    Returns recipients in the Clinical Awareness Group:
      MD, DPCS, CASE_MANAGER, ASSIGNED_RN, ASSIGNED_LVN

    NOTE:
    This implementation is a placeholder until you wire actual assignment tables.
    For now, it selects:
      - all MD/Administrator as MD/DPCS (adjust roles to your system)
      - does not guess RN/LVN assignments
    """

    recipients: List[Dict[str, str]] = []

    # Minimal safe approach: notify MD/NP/Administrator group for now
    md_like = (
        db.query(User)
        .filter(User.tenant_id == tenant_id)
        .filter(User.active.is_(True))
        .filter(User.role.in_(["MD", "NP", "Administrator", "DPCS"]))
        .all()
    )

    for u in md_like:
        recipients.append({"user_id": str(u.id), "role": str(u.role)})

    return recipients