# app/api/order_templates.py

"""
Order-set template ("pack") endpoints: list/create packs, add/remove items,
and the key "Import Pack" action that bulk-creates real orders on a patient
chart from a template (mirrors HospiceMD's template-picker + Import Pack
button, but generalized to any order type and any tenant-authored pack).
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import CurrentUser
from app.core.database import get_db
from app.core.permissions import require_roles
from app.core.patient_access import get_authorized_patient
from app.models.order_template import OrderTemplate, OrderTemplateItem
from app.models.patient import Patient
from app.services import order_template_service as svc
from app.services.physician_order_service import PhysicianOrderError

router = APIRouter(prefix="/order-templates", tags=["order-templates"])

CLINICAL_ROLES = ["LVN", "RN", "NP", "MD", "Surveyor"]


class TemplateCreate(BaseModel):
    name: str
    description: str | None = None


class TemplateItemCreate(BaseModel):
    order_type: str
    sub_type: str | None = "NEW"
    order_text: str
    strength: str | None = None
    dosage: str | None = None
    route: str | None = None
    frequency: str | None = None
    indication: str | None = None
    quantity: str | None = None
    payer: str | None = None
    vendor: str | None = None
    administered_by: str | None = None
    special_instruction: str | None = None
    sort_order: int | None = None


class ImportRequest(BaseModel):
    patient_id: uuid.UUID
    start_date: date | None = None
    # Same attestation required for any manually-entered physician order (see
    # OrdersHubCard's "Physician Sign-Off" section) — a pack is just a fast way
    # to fill out that same form N times, so it must carry the same required
    # ordering-provider attribution before each item can be submitted for MD approval.
    ordered_by_provider_name: str
    ordered_by_provider_role: str = "MD"
    source_type: str = "WRITTEN"
    prescriber_authenticated: bool = True
    phone_readback_confirmed: bool | None = None


def _serialize_item(item: OrderTemplateItem) -> dict:
    return {
        "id": str(item.id),
        "order_type": item.order_type,
        "sub_type": item.sub_type,
        "order_text": item.order_text,
        "strength": item.strength,
        "dosage": item.dosage,
        "route": item.route,
        "frequency": item.frequency,
        "indication": item.indication,
        "quantity": item.quantity,
        "payer": item.payer,
        "vendor": item.vendor,
        "administered_by": item.administered_by,
        "special_instruction": item.special_instruction,
        "sort_order": item.sort_order,
    }


def _serialize_template(template: OrderTemplate, include_items: bool = True) -> dict:
    data = {
        "id": str(template.id),
        "name": template.name,
        "description": template.description,
        "is_system": template.is_system,
        "tenant_id": str(template.tenant_id) if template.tenant_id else None,
        "item_count": len(template.items),
    }
    if include_items:
        data["items"] = [_serialize_item(i) for i in template.items]
    return data


@router.get("", summary="List order-set templates visible to this tenant (system packs + own packs)")
def list_templates(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    templates = svc.list_templates(db, user.tenant_id)
    return [_serialize_template(t, include_items=False) for t in templates]


def _authorize_template(template: OrderTemplate, user: CurrentUser) -> None:
    """A template is visible/usable if it's a shared system template
    (tenant_id is NULL) or belongs to the caller's own tenant."""
    if template.tenant_id is not None and template.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Template not found")


@router.get("/{template_id}", summary="Get a template with its full item list")
def get_template(
    template_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    template = svc.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    _authorize_template(template, user)
    return _serialize_template(template)


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a new (tenant-owned) order template")
def create_template(
    payload: TemplateCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    template = svc.create_template(
        db,
        tenant_id=user.tenant_id,
        name=payload.name,
        description=payload.description,
        created_by=user.user_id,
        is_system=False,
    )
    return _serialize_template(template)


@router.post("/{template_id}/items", status_code=status.HTTP_201_CREATED, summary="Add an item to a template")
def add_item(
    template_id: uuid.UUID,
    payload: TemplateItemCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    template = svc.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    _authorize_template(template, user)
    if template.is_system:
        raise HTTPException(status_code=403, detail="System templates cannot be modified")
    try:
        item = svc.add_template_item(db, template_id, payload.model_dump(), created_by=user.user_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _serialize_item(item)


@router.delete("/{template_id}/items/{item_id}", summary="Remove an item from a template")
def delete_item(
    template_id: uuid.UUID,
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    template = svc.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    _authorize_template(template, user)
    if template.is_system:
        raise HTTPException(status_code=403, detail="System templates cannot be modified")
    svc.delete_template_item(db, item_id)
    return {"status": "deleted"}


@router.delete("/{template_id}", summary="Delete a tenant-owned template")
def delete_template(
    template_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    template = svc.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    _authorize_template(template, user)
    if template.is_system:
        raise HTTPException(status_code=403, detail="System templates cannot be deleted")
    svc.delete_template(db, template_id)
    return {"status": "deleted"}


@router.post("/{template_id}/import", summary="Import Pack: bulk-create every template item on a patient chart")
def import_template(
    template_id: uuid.UUID,
    payload: ImportRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    patient = get_authorized_patient(db, payload.patient_id, user)

    template = svc.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    _authorize_template(template, user)

    try:
        result = svc.import_template(
            db,
            template_id=template_id,
            patient_id=payload.patient_id,
            user=user,
            start_date=payload.start_date,
            ordered_by_provider_name=payload.ordered_by_provider_name,
            ordered_by_provider_role=payload.ordered_by_provider_role,
            source_type=payload.source_type,
            prescriber_authenticated=payload.prescriber_authenticated,
            phone_readback_confirmed=payload.phone_readback_confirmed,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PhysicianOrderError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return result
