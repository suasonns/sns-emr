# app/services/order_template_service.py

"""
Order-set template ("pack") service: CRUD for reusable named order sets, and
bulk import of a template's items into a real patient chart.

Every item — regardless of order type (MEDICATION/DME/SUPPLY/LAB/TREATMENT/
DIET/OTHER) — is imported as a real `PhysicianOrder` through the same
DRAFT -> PENDING_HOSPICE_MD_APPROVAL pipeline used by a manually-entered
Orders Hub order, so it shows up in the exact same list, in the exact same
order_text format, and still requires MD sign-off (or immediate verbal-order
execution) before it can be executed. Medication-type items additionally get
a mirrored row in the legacy `Medication` table purely so they still run
through the allergy/interaction drug-safety engine.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.order_template import OrderTemplate, OrderTemplateItem
from app.models.medication import Medication
from app.services import physician_order_service
from app.services.drug_safety_service import check_new_medication_safety
from app.services.audit_logger import log_event
from app.utils.med_normalization import normalize_text

MEDICATION_TYPE = "MEDICATION"
ORDER_TYPES = {"MEDICATION", "DME", "SUPPLY", "LAB", "TREATMENT", "DIET", "OTHER"}
SUB_TYPES = {"NEW", "REFILL", "DC", "PRE_ADMIT"}


def list_templates(db: Session, tenant_id: Optional[uuid.UUID]) -> list[OrderTemplate]:
    """System templates (tenant_id IS NULL) + this tenant's own templates."""
    q = db.query(OrderTemplate)
    if tenant_id is not None:
        q = q.filter((OrderTemplate.tenant_id == tenant_id) | (OrderTemplate.tenant_id.is_(None)))
    else:
        q = q.filter(OrderTemplate.tenant_id.is_(None))
    return q.order_by(OrderTemplate.is_system.desc(), OrderTemplate.name.asc()).all()


def get_template(db: Session, template_id: uuid.UUID) -> Optional[OrderTemplate]:
    return db.query(OrderTemplate).filter(OrderTemplate.id == template_id).first()


def create_template(
    db: Session, *, tenant_id: Optional[uuid.UUID], name: str, description: str | None, created_by, is_system: bool = False
) -> OrderTemplate:
    template = OrderTemplate(
        tenant_id=tenant_id,
        name=(name or "").strip(),
        description=(description or "").strip() or None,
        is_system=is_system,
        created_by=created_by,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def add_template_item(db: Session, template_id: uuid.UUID, item: dict, created_by=None) -> OrderTemplateItem:
    order_type = (item.get("order_type") or "").strip().upper()
    if order_type not in ORDER_TYPES:
        raise ValueError(f"order_type must be one of {sorted(ORDER_TYPES)}")

    sub_type = (item.get("sub_type") or "NEW").strip().upper()
    if sub_type not in SUB_TYPES:
        sub_type = "NEW"

    max_sort = (
        db.query(OrderTemplateItem.sort_order)
        .filter(OrderTemplateItem.template_id == template_id)
        .order_by(OrderTemplateItem.sort_order.desc())
        .first()
    )
    next_sort = (max_sort[0] + 1) if max_sort else 0

    row = OrderTemplateItem(
        template_id=template_id,
        order_type=order_type,
        sub_type=sub_type,
        order_text=(item.get("order_text") or "").strip(),
        strength=item.get("strength"),
        dosage=item.get("dosage"),
        route=item.get("route"),
        frequency=item.get("frequency"),
        indication=item.get("indication"),
        quantity=item.get("quantity"),
        payer=item.get("payer"),
        vendor=item.get("vendor"),
        administered_by=item.get("administered_by"),
        special_instruction=item.get("special_instruction"),
        start_date=item.get("start_date"),
        stop_date=item.get("stop_date"),
        sort_order=item.get("sort_order", next_sort),
        created_by=created_by,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete_template(db: Session, template_id: uuid.UUID) -> None:
    template = get_template(db, template_id)
    if template:
        db.delete(template)
        db.commit()


def delete_template_item(db: Session, item_id: uuid.UUID) -> None:
    item = db.query(OrderTemplateItem).filter(OrderTemplateItem.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()


def _format_order_text(item: OrderTemplateItem) -> str:
    """Builds the exact same concatenated order_text string that OrdersHubCard's
    handleAddOrder() builds for a manually-entered order, so an imported pack
    item is indistinguishable in format from one typed in by hand."""
    parts = [
        item.order_text,
        item.strength and f"Strength: {item.strength}",
        item.dosage and f"Dosage/Qty: {item.dosage}",
        item.route and f"Route: {item.route}",
        item.frequency and f"Frequency: {item.frequency}",
        item.indication and f"Indication: {item.indication}",
        item.payer and f"Payer: {item.payer}",
        item.vendor and f"Vendor: {item.vendor}",
        item.administered_by and f"Administered by: {item.administered_by}",
        item.start_date and f"Start Date: {item.start_date.isoformat()}",
        item.stop_date and f"Stop Date: {item.stop_date.isoformat()}",
        item.special_instruction and f"Instructions: {item.special_instruction}",
    ]
    return " — ".join(p.strip() for p in parts if p and p.strip())


def import_template(
    db: Session,
    *,
    template_id: uuid.UUID,
    patient_id: uuid.UUID,
    user,
    start_date: date | None = None,
    ordered_by_provider_name: str,
    ordered_by_provider_role: str = "MD",
    source_type: str = "WRITTEN",
    prescriber_authenticated: bool = True,
    phone_readback_confirmed: bool | None = None,
) -> dict:
    """
    Bulk-import every item in a template as a real signed physician order —
    each item goes through the exact same DRAFT -> PENDING_HOSPICE_MD_APPROVAL
    pipeline (physician_order_service.create_draft + submit_for_approval) as a
    manually-entered Orders Hub order, so imported items appear in the same
    list, in the same order_text format, and still require MD sign-off before
    they can be executed (or immediate verbal-order execution, if applicable)
    — a pack is just a fast way to fill out that same form N times.

    ordered_at is always "now" (the moment of import), not the template's
    original authoring date or the care start_date — the order is being
    placed today, even if care starts on a different date.

    Medication-type items also get a mirrored row in the legacy `Medication`
    table so they still run through the allergy/interaction safety engine.
    """
    template = get_template(db, template_id)
    if not template:
        raise ValueError("Template not found")

    effective_start = start_date or date.today()
    imported_at = datetime.now(timezone.utc)
    created_medications: list[dict] = []
    created_orders: list[dict] = []

    for item in template.items:
        order_text = _format_order_text(item)

        draft = physician_order_service.create_draft(
            db,
            tenant_id=user.tenant_id,
            patient_id=patient_id,
            order_text=order_text,
            order_category=item.order_type,
            source_type=source_type,
            ordered_by_provider_name=ordered_by_provider_name,
            ordered_by_provider_role=ordered_by_provider_role,
            ordered_at=imported_at,
            prescriber_authenticated=prescriber_authenticated,
            phone_readback_confirmed=phone_readback_confirmed,
            created_by=user.user_id,
        )
        order = physician_order_service.submit_for_approval(db, order=draft, submitted_by=user.user_id)
        created_orders.append(
            {
                "order_id": str(order.id),
                "order_type": order.order_category,
                "order_text": order.order_text,
            }
        )

        if item.order_type == MEDICATION_TYPE:
            med_name = (item.order_text or "").strip()
            medication = Medication(
                patient_id=patient_id,
                medication_name=med_name,
                canonical_name=normalize_text(med_name),
                dosage=(item.dosage or "").strip() or "N/A",
                route=(item.route or "").strip() or "N/A",
                frequency=(item.frequency or "").strip() or "N/A",
                start_date=effective_start,
                end_date=None,
                created_by=user.user_id,
                # Link back to the signed PhysicianOrder so the Current
                # Medications list can show real approval/signature status
                # instead of implying it's already MD-approved.
                physician_order_id=order.id,
            )
            db.add(medication)
            db.commit()
            db.refresh(medication)

            safety = check_new_medication_safety(db, patient_id, med_name)
            created_medications.append(
                {
                    "medication_id": str(medication.id),
                    "medication_name": medication.medication_name,
                    "allergy_alerts": safety.get("allergy_alerts", []),
                    "interaction_alerts": safety.get("interaction_alerts", []),
                }
            )

    log_event(
        user_id=user.user_id,
        role=user.role,
        action="IMPORT_ORDER_TEMPLATE",
        entity_type="order_template",
        entity_id=str(template.id),
        metadata={"patient_id": str(patient_id), "item_count": len(template.items)},
    )

    return {
        "template_id": str(template.id),
        "template_name": template.name,
        "patient_id": str(patient_id),
        "medications_created": created_medications,
        "orders_created": created_orders,
        "total_imported": len(created_orders),
    }
