from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.services.task_overdue_engine import mark_overdue_tasks

router = APIRouter(prefix="/internal/tasks", tags=["internal-tasks"])


# =========================================================
# AUTH GUARD
# =========================================================
def require_super_user(current_user) -> None:
    """
    Enterprise-safe internal gate.
    Matches internal_superuser.py behavior: SUPER_USER only.
    """
    role = (
        current_user.get("role")
        if isinstance(current_user, dict)
        else getattr(current_user, "role", None)
    )

    if str(role).upper() != "SUPER_USER":
        raise HTTPException(status_code=403, detail="Forbidden")


# =========================================================
# OVERDUE TASK RUNNER
# =========================================================
@router.post(
    "/overdue/run",
    status_code=status.HTTP_200_OK,
    summary="Run overdue task transition for current tenant (SUPER_USER only)",
)
def run_overdue_tasks(
    *,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Internal-only endpoint.

    Transitions ACTIVE tasks to OVERDUE for the current tenant
    based on due_date < now (UTC).

    ACTIVE tasks = PENDING, IN_PROGRESS, OVERDUE (handled in service layer)
    """

    require_super_user(current_user)

    # -----------------------------------------------------
    # CONTEXT EXTRACTION (SAFE)
    # -----------------------------------------------------
    tenant_id: UUID | None = (
        current_user.get("tenant_id")
        if isinstance(current_user, dict)
        else getattr(current_user, "tenant_id", None)
    )

    user_id: UUID | None = (
        current_user.get("user_id")
        if isinstance(current_user, dict)
        else getattr(current_user, "id", None)
    )

    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context missing")

    if not user_id:
        raise HTTPException(status_code=400, detail="User context missing")

    # -----------------------------------------------------
    # EXECUTE OVERDUE TRANSITION
    # -----------------------------------------------------
    result = mark_overdue_tasks(db=db, tenant_id=tenant_id)

    if not isinstance(result, dict):
        raise HTTPException(
            status_code=500,
            detail="Invalid response from overdue task engine",
        )

    # -----------------------------------------------------
    # RESPONSE (AUDIT SAFE)
    # -----------------------------------------------------
    return {
        "tenant_id": str(tenant_id),
        "executed_by": str(user_id),
        "action": "OVERDUE_TRANSITION",
        "marked_overdue": result.get("marked_overdue", 0),
        "as_of_utc": result.get("as_of_utc"),
    }
