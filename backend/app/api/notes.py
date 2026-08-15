from __future__ import annotations

from datetime import datetime
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db_tenant_dependency import get_db_tenant
from app.core.security import get_current_user
from app.models.clinical_note import ClinicalNote
from app.services.audit_logger import log_event
from app.services.clinical_note_service import (
    finalize_clinical_note as finalize_note_service,
)


router = APIRouter(prefix="/notes", tags=["notes"])


# =========================================================
# CURRENT USER RESOLUTION
# =========================================================

def _current_user_id(db: Session, user: Any) -> uuid.UUID:
    """
    Resolve CurrentUser into the real users.id UUID.

    CurrentUser is not guaranteed to be the SQLAlchemy User model.
    Do not use user.id directly unless it exists.
    """

    for attr_name in (
        "id",
        "user_id",
        "user_uuid",
        "sub",
    ):
        value = getattr(user, attr_name, None)

        if not value:
            continue

        try:
            return uuid.UUID(str(value))
        except (TypeError, ValueError):
            continue

    email = getattr(user, "email", None)

    if email:
        found_user_id = db.execute(
            text(
                """
                SELECT id
                FROM users
                WHERE lower(email) = lower(:email)
                LIMIT 1
                """
            ),
            {"email": email},
        ).scalar_one_or_none()

        if found_user_id:
            return uuid.UUID(str(found_user_id))

    raise HTTPException(
        status_code=401,
        detail="Authenticated user could not be resolved to users.id",
    )


def _tenant_id(user: Any) -> uuid.UUID:
    tenant_id = getattr(user, "tenant_id", None)

    if not tenant_id:
        raise HTTPException(
            status_code=401,
            detail="Authenticated user has no tenant_id",
        )

    return uuid.UUID(str(tenant_id))


# =========================================================
# HELPERS
# =========================================================

def _require_role(user_role: str, allowed: set[str]) -> None:
    if (user_role or "").upper() not in allowed:
        raise HTTPException(status_code=403, detail="Forbidden")


def _get_note_or_404(
    *,
    db: Session,
    note_id: uuid.UUID,
    tenant_id: uuid.UUID,
    for_update: bool = False,
) -> ClinicalNote:
    query = db.query(ClinicalNote)

    if for_update:
        query = query.with_for_update()

    note = (
        query
        .filter(
            ClinicalNote.id == note_id,
            ClinicalNote.tenant_id == tenant_id,
        )
        .first()
    )

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return note


# =========================================================
# COUNTERSIGN
# =========================================================

@router.post("/{note_id}/countersign")
def countersign_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    role = (getattr(user, "role", "") or "").upper()

    if role not in {"MSW", "LCSW"}:
        raise HTTPException(status_code=403, detail="Only MSW/LCSW allowed")

    actor_user_id = _current_user_id(db, user)
    tenant_id = _tenant_id(user)

    note = _get_note_or_404(
        db=db,
        note_id=note_id,
        tenant_id=tenant_id,
        for_update=True,
    )

    if note.finalized_at:
        raise HTTPException(status_code=400, detail="Cannot modify finalized note")

    if note.discipline != "BSW":
        raise HTTPException(status_code=400, detail="Not a BSW note")

    if note.countersigned_by:
        raise HTTPException(status_code=400, detail="Already countersigned")

    now = datetime.utcnow()

    note.countersigned_by = actor_user_id
    note.countersigned_at = now
    note.updated_at = now

    db.flush()

    log_event(
        user_id=actor_user_id,
        role=role,
        action="COUNTERSIGN_NOTE",
        entity_type="clinical_note",
        entity_id=str(note.id),
        db=db,
    )

    db.commit()
    db.refresh(note)

    return {
        "note_id": str(note.id),
        "status": "COUNTERSIGNED",
    }


# =========================================================
# FINALIZE NOTE
# =========================================================

@router.post("/{note_id}/finalize")
def finalize_clinical_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    role = (getattr(user, "role", "") or "").upper()

    _require_role(
        role,
        {"RN", "NP", "MD", "ADMIN", "SC", "MSW", "LCSW"},
    )

    actor_user_id = _current_user_id(db, user)
    tenant_id = _tenant_id(user)

    note = _get_note_or_404(
        db=db,
        note_id=note_id,
        tenant_id=tenant_id,
        for_update=True,
    )

    if note.finalized_at:
        raise HTTPException(status_code=400, detail="Already finalized")

    updated_note, validation_result = finalize_note_service(
        db=db,
        note=note,
        user_id=actor_user_id,
    )

    return {
        "note_id": str(updated_note.id),
        "status": updated_note.status,
        "validation": (
            updated_note.content.get("_validation")
            if isinstance(updated_note.content, dict)
            else None
        ),
    }