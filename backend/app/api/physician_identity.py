"""Administrative endpoints for Physician Identity Mapping.

Owner directive (2026-08-21): only an authorized administrator may create or
end a User-to-Physician linkage. This is the ONLY path that grants
provider-identity access (see app/services/physician_identity_service.py for
the fail-closed enforcement this linkage gates).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import CurrentUser
from app.core.database import get_db
from app.core.permissions import require_roles
from app.models.physician import Physician
from app.models.user import User
from app.services import physician_identity_service as svc

router = APIRouter(prefix="/physician-identity", tags=["physician-identity"])

ADMIN_ROLES = {"ADMIN", "ADMINISTRATOR", "DPCS", "DPCS_ADMINISTRATOR"}


class LinkRequest(BaseModel):
    user_id: uuid.UUID
    physician_id: uuid.UUID
    reason: str


class UnlinkRequest(BaseModel):
    user_id: uuid.UUID
    reason: str


def _serialize(target_user: User) -> dict:
    return {
        "user_id": str(target_user.id),
        "physician_id": str(target_user.physician_id) if target_user.physician_id else None,
        "physician_link_status": target_user.physician_link_status,
        "physician_linked_by_user_id": (
            str(target_user.physician_linked_by_user_id) if target_user.physician_linked_by_user_id else None
        ),
        "physician_linked_at": target_user.physician_linked_at.isoformat() if target_user.physician_linked_at else None,
        "physician_linkage_verified_at": (
            target_user.physician_linkage_verified_at.isoformat()
            if target_user.physician_linkage_verified_at else None
        ),
    }


@router.post("/link", summary="Administrator: link and verify a User account to a Physician directory record")
def link_physician(
    payload: LinkRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(ADMIN_ROLES, allow_clinical_admin=False)),
):
    target_user = db.query(User).filter(User.id == payload.user_id, User.tenant_id == user.tenant_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    physician = db.query(Physician).filter(
        Physician.id == payload.physician_id, Physician.tenant_id == user.tenant_id
    ).first()
    if not physician:
        raise HTTPException(status_code=404, detail="Physician directory record not found")

    try:
        target_user = svc.link_physician(
            db,
            tenant_id=user.tenant_id,
            target_user=target_user,
            physician=physician,
            linked_by_user_id=user.user_id,
            reason=payload.reason,
        )
    except svc.PhysicianIdentityError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    db.commit()
    return _serialize(target_user)


@router.post("/unlink", summary="Administrator: end an active User-to-Physician linkage")
def unlink_physician(
    payload: UnlinkRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(ADMIN_ROLES, allow_clinical_admin=False)),
):
    target_user = db.query(User).filter(User.id == payload.user_id, User.tenant_id == user.tenant_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        target_user = svc.unlink_physician(
            db,
            tenant_id=user.tenant_id,
            target_user=target_user,
            unlinked_by_user_id=user.user_id,
            reason=payload.reason,
        )
    except svc.PhysicianIdentityError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    db.commit()
    return _serialize(target_user)


@router.get("/status/{user_id}", summary="Administrator: view a User's physician linkage status")
def linkage_status(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(ADMIN_ROLES, allow_clinical_admin=False)),
):
    target_user = db.query(User).filter(User.id == user_id, User.tenant_id == user.tenant_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    return _serialize(target_user)
