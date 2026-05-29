# app/tenancy/context.py

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.tenancy.registry import assert_known_tenant
from app.db_tenant_dependency import get_db_tenant


def require_valid_tenant(user=Depends(get_current_user)):
    """
    Enterprise-grade tenant safety guard:
    - requires tenant_id present on authenticated user
    - requires tenant_id exists in canonical tenant registry
    """
    tenant_id = getattr(user, "tenant_id", None)
    if tenant_id is None and isinstance(user, dict):
        tenant_id = user.get("tenant_id")

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing tenant context",
        )

    try:
        assert_known_tenant(str(tenant_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    return user


def set_tenant_context(
    db: Session = Depends(get_db_tenant),
    user=Depends(require_valid_tenant),
):
    """
    Request-scoped tenant context initializer (DEV-mode compliant).

    Stores:
      db.info["tenant_id"]
      db.info["user_id"]

    NOTE:
    - ORM-only tenant context
    - No DB GUCs (set_config)
    - No RLS dependency
    """
    db.info["tenant_id"] = str(getattr(user, "tenant_id"))
    db.info["user_id"] = str(getattr(user, "id"))

    return user


def get_tenant_id(db: Session) -> str:
    """
    Canonical ORM tenant accessor. Fails closed.
    """
    tenant_id = db.info.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing tenant context in DB session",
        )
    return str(tenant_id)


def get_user_id(db: Session) -> str:
    """
    Canonical ORM user accessor. Fails closed.
    """
    user_id = db.info.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing user context in DB session",
        )
    return str(user_id)