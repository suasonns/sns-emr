# app/db_request_dependency.py
from __future__ import annotations

from typing import Generator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.db_tenant_dependency import get_db_tenant


def get_db_tenant_with_request_state(
    request: Request,
    db: Session = Depends(get_db_tenant),
) -> Generator[Session, None, None]:
    """
    Enterprise-safe DB dependency wrapper.

    - Uses the canonical tenant DB dependency (get_db_tenant)
    - Attaches db to request.state.db so audit middleware can see it
    - Does not change tenancy behavior
    """
    request.state.db = db
    try:
        yield db
    finally:
        # get_db_tenant handles cleanup; don't double-close here
        pass