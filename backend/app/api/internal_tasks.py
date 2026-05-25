from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.services.task_overdue_engine import mark_overdue_tasks

router = APIRouter(prefix="/internal/tasks", tags=["internal-tasks"])


def require_super_user(current_user) -> None:
    """
    Enterprise-safe internal gate.
    Matches internal_superuser.py behavior: SUPER_USER only.
    """
    role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, "role", None)
    if str(role).upper() != "SUPER_USER":
        raise HTTPException(status_code=403, detail="Forbidden")


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

    Transitions OPEN tasks to OVERDUE for the current tenant
    based on due_date < now (UTC).
    """
    require_super_user(current_user)

    tenant_id: UUID | None = (
        current_user.get("tenant_id") if isinstance(current_user, dict) else getattr(current_user, "tenant_id", None)
    )
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context missing")

    result = mark_overdue_tasks(db=db, tenant_id=tenant_id)

    return {
        "tenant_id": str(tenant_id),
        "marked_overdue": result["marked_overdue"],
        "as_of_utc": result["as_of_utc"],
    }