from fastapi import HTTPException

from app.domain.visits import normalize_visit_type


def authorize_documentation(
    *,
    user_role: str,
    visit_type: str,
    allow_nursing_override: bool = True,
    action: str = "document",
):
    """
    Enforces discipline-scoped documentation.

    Rules:
    - A user may document only within their discipline.
    - RN / NP / MD may supervise and document across disciplines.
    - CHHA (AIDE) may only document aide visits.
    - Volunteers may only document volunteer services.
    """

    role = user_role.strip().upper()
    vt = normalize_visit_type(visit_type)

    # ---------------------------------------------------------
    # Nursing override (supervision authority)
    # ---------------------------------------------------------
    if allow_nursing_override and role in {"RN", "NP", "MD"}:
        return

    # ---------------------------------------------------------
    # Exact discipline match required
    # ---------------------------------------------------------
    if role != vt:
        raise HTTPException(
            status_code=403,
            detail=f"You may only {action} records pertaining to your discipline",
        )