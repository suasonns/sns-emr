from __future__ import annotations

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.form_registry_model import FormRegistryModel
from app.models.form_module import FormModule
from app.models.form_package_module import FormPackageModule


router = APIRouter(prefix="/forms", tags=["Forms"])


# =========================================================
# DB DEPENDENCY
# =========================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================================
# REQUEST / RESPONSE SCHEMAS
# =========================================================
class VisitRequest(BaseModel):
    patient_id: str
    visit_type: str
    form_type: Optional[str] = None
    level_of_care: Optional[str] = None
    visit_schedule_type: Optional[str] = None
    event_type: Optional[str] = None


class ModuleResponse(BaseModel):
    name: str
    module_key: str


class FormResolveResponse(BaseModel):
    form_key: str
    form_type: str
    discipline: str
    form_family: str
    modules: List[ModuleResponse]


# =========================================================
# HELPERS
# =========================================================
def _normalize_discipline(value: str) -> str:
    return (value or "").strip().upper()


# =========================================================
# ROUTE
# =========================================================
@router.post("/resolve", response_model=FormResolveResponse)
def resolve_form(payload: VisitRequest, db: Session = Depends(get_db)):
    """
    Resolve the active primary form for a discipline and return attached modules.

    Phase 1 behavior:
    - discipline-driven
    - primary active form only
    - module list driven by DB mapping
    """
    discipline = _normalize_discipline(payload.visit_type)

    if not discipline:
        raise HTTPException(status_code=422, detail="visit_type is required")

    # -----------------------------------------------------
    # FIND PRIMARY ACTIVE FORM
    # -----------------------------------------------------
    form = (
        db.query(FormRegistryModel)
        .filter(FormRegistryModel.discipline == discipline)
        .filter(FormRegistryModel.is_primary == True)   # noqa: E712
        .filter(FormRegistryModel.is_active == True)    # noqa: E712
        .order_by(FormRegistryModel.created_at.asc())
        .first()
    )

    if not form:
        raise HTTPException(
            status_code=404,
            detail=f"No active primary form found for discipline '{discipline}'",
        )

    # -----------------------------------------------------
    # LOAD MODULES
    # -----------------------------------------------------
    modules = (
        db.query(FormModule.name, FormModule.module_key)
        .join(
            FormPackageModule,
            FormPackageModule.module_id == FormModule.id,
        )
        .filter(FormPackageModule.form_registry_id == form.id)
        .order_by(FormModule.name.asc())
        .all()
    )

    return {
        "form_key": form.form_key,
        "form_type": form.form_type,
        "discipline": form.discipline,
        "form_family": form.form_family,
        "modules": [
            {
                "name": row.name,
                "module_key": row.module_key,
            }
            for row in modules
        ],
    }