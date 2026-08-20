from __future__ import annotations

import uuid
import json
from datetime import datetime, timezone
from urllib import parse, request
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.patients import get_db_with_request_state, require_tenant_user, _tenant_id_uuid
from app.models.physician import Physician, PhysicianPecosCache

router = APIRouter(prefix="/physicians", tags=["physicians"])

NPI_LOOKUP_URL = "https://npiregistry.cms.hhs.gov/api/"
VALID_PHYSICIAN_STATUSES = {"active", "inactive"}
VALID_LIST_STATUSES = {"active", "inactive", "both"}


class PhysicianWrite(BaseModel):
    npi: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    display_name: str | None = None
    title: str | None = None
    specialty_type: str | None = None
    license_number: str | None = None
    taxonomy_code: str | None = None
    address_street: str | None = None
    address_suite: str | None = None
    address_city: str | None = None
    address_state: str | None = None
    address_zip: str | None = None
    phone: str | None = None
    fax: str | None = None
    email: str | None = None
    contact_name: str | None = None
    protocol_notes: str | None = None
    status: str = "active"
    register_for_eprescription: bool = False
    pecos_status: str | None = None
    pecos_checked_at: datetime | None = None


def _actor_id(user) -> uuid.UUID:
    raw_actor_id = getattr(user, "user_id", None) or getattr(user, "id", None)
    if not raw_actor_id:
        raise HTTPException(status_code=500, detail="Invalid user identity")
    return uuid.UUID(str(raw_actor_id))


def _normalize_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = str(value).strip()
    return trimmed or None


def _normalize_npi(value: str | None) -> str | None:
    cleaned = "".join(ch for ch in str(value or "") if ch.isdigit())
    return cleaned or None


def _build_display_name(display_name: str | None, first_name: str | None, last_name: str | None) -> str:
    explicit = _normalize_optional_string(display_name)
    if explicit:
        return explicit
    parts = [
        _normalize_optional_string(first_name),
        _normalize_optional_string(last_name),
    ]
    combined = " ".join(part for part in parts if part)
    if combined:
        return combined
    raise HTTPException(status_code=400, detail="Physician name is required")


def _serialize_physician(physician: Physician) -> dict[str, Any]:
    return {
        "id": str(physician.id),
        "tenant_id": str(physician.tenant_id),
        "npi": physician.npi,
        "first_name": physician.first_name,
        "last_name": physician.last_name,
        "display_name": physician.display_name,
        "title": physician.title,
        "specialty_type": physician.specialty_type,
        "license_number": physician.license_number,
        "taxonomy_code": physician.taxonomy_code,
        "address_street": physician.address_street,
        "address_suite": physician.address_suite,
        "address_city": physician.address_city,
        "address_state": physician.address_state,
        "address_zip": physician.address_zip,
        "phone": physician.phone,
        "fax": physician.fax,
        "email": physician.email,
        "contact_name": physician.contact_name,
        "protocol_notes": physician.protocol_notes,
        "status": physician.status,
        "register_for_eprescription": physician.register_for_eprescription,
        "pecos_status": physician.pecos_status,
        "pecos_checked_at": physician.pecos_checked_at,
        "created_at": physician.created_at,
        "created_by": str(physician.created_by) if physician.created_by else None,
        "updated_at": physician.updated_at,
        "updated_by": str(physician.updated_by) if physician.updated_by else None,
    }


def _apply_physician_payload(physician: Physician, payload: PhysicianWrite) -> None:
    physician.npi = _normalize_npi(payload.npi)
    physician.first_name = _normalize_optional_string(payload.first_name)
    physician.last_name = _normalize_optional_string(payload.last_name)
    physician.display_name = _build_display_name(
        payload.display_name,
        physician.first_name,
        physician.last_name,
    )
    physician.title = _normalize_optional_string(payload.title)
    physician.specialty_type = _normalize_optional_string(payload.specialty_type)
    physician.license_number = _normalize_optional_string(payload.license_number)
    physician.taxonomy_code = _normalize_optional_string(payload.taxonomy_code)
    physician.address_street = _normalize_optional_string(payload.address_street)
    physician.address_suite = _normalize_optional_string(payload.address_suite)
    physician.address_city = _normalize_optional_string(payload.address_city)
    physician.address_state = _normalize_optional_string(payload.address_state)
    physician.address_zip = _normalize_optional_string(payload.address_zip)
    physician.phone = _normalize_optional_string(payload.phone)
    physician.fax = _normalize_optional_string(payload.fax)
    physician.email = _normalize_optional_string(payload.email)
    physician.contact_name = _normalize_optional_string(payload.contact_name)
    physician.protocol_notes = _normalize_optional_string(payload.protocol_notes)
    normalized_status = (_normalize_optional_string(payload.status) or "active").lower()
    if normalized_status not in VALID_PHYSICIAN_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid physician status")
    physician.status = normalized_status
    physician.register_for_eprescription = bool(payload.register_for_eprescription)
    physician.pecos_status = _normalize_optional_string(payload.pecos_status)
    physician.pecos_checked_at = payload.pecos_checked_at


def _pick_primary_taxonomy(taxonomies: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not taxonomies:
        return None
    for taxonomy in taxonomies:
        if taxonomy.get("primary"):
            return taxonomy
    return taxonomies[0]


def _pick_best_address(addresses: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not addresses:
        return None
    for address in addresses:
        purpose = str(address.get("address_purpose") or "").upper()
        if purpose == "LOCATION":
            return address
    return addresses[0]


@router.get("")
def list_physicians(
    status: str = Query("active"),
    type: str | None = Query(default=None),
    specialty: str | None = Query(default=None),
    name: str | None = Query(default=None),
    license_number: str | None = Query(default=None),
    npi: str | None = Query(default=None),
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    normalized_status = (status or "active").strip().lower()
    if normalized_status not in VALID_LIST_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status filter")

    query = db.query(Physician).filter(Physician.tenant_id == tenant_id)

    if normalized_status != "both":
        query = query.filter(Physician.status == normalized_status)

    specialty_filter = _normalize_optional_string(type) or _normalize_optional_string(specialty)
    if specialty_filter:
        query = query.filter(Physician.specialty_type.ilike(f"%{specialty_filter}%"))

    normalized_name = _normalize_optional_string(name)
    if normalized_name:
        query = query.filter(
            or_(
                Physician.display_name.ilike(f"%{normalized_name}%"),
                Physician.first_name.ilike(f"%{normalized_name}%"),
                Physician.last_name.ilike(f"%{normalized_name}%"),
            )
        )

    normalized_license = _normalize_optional_string(license_number)
    if normalized_license:
        query = query.filter(Physician.license_number.ilike(f"%{normalized_license}%"))

    normalized_npi = _normalize_optional_string(npi)
    if normalized_npi:
        query = query.filter(Physician.npi.ilike(f"%{normalized_npi}%"))

    physicians = (
        query.order_by(
            Physician.display_name.asc(),
            Physician.last_name.asc(),
            Physician.first_name.asc(),
        )
        .all()
    )
    return [_serialize_physician(physician) for physician in physicians]


@router.get("/npi-lookup")
def physician_npi_lookup(
    npi: str,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    _tenant_id_uuid(user)
    normalized_npi = _normalize_npi(npi)
    if not normalized_npi:
        return {"found": False, "error": "NPI is required"}

    try:
        lookup_url = f"{NPI_LOOKUP_URL}?{parse.urlencode({'version': '2.1', 'number': normalized_npi})}"
        with request.urlopen(lookup_url, timeout=10.0) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # pragma: no cover - network dependent
        return {"found": False, "error": f"NPI lookup unavailable: {exc}"}

    results = payload.get("results") or []
    if not results:
        return {"found": False}

    result = results[0]
    basic = result.get("basic") or {}
    taxonomy = _pick_primary_taxonomy(result.get("taxonomies") or []) or {}
    address = _pick_best_address(result.get("addresses") or []) or {}

    address_parts = [
        str(address.get("address_1") or "").strip(),
        str(address.get("address_2") or "").strip(),
    ]
    address_street = ", ".join(part for part in address_parts if part) or None

    return {
        "found": True,
        "first_name": _normalize_optional_string(basic.get("first_name")),
        "last_name": _normalize_optional_string(basic.get("last_name")),
        "credential": _normalize_optional_string(basic.get("credential")),
        "taxonomy_description": _normalize_optional_string(taxonomy.get("desc")),
        "taxonomy_code": _normalize_optional_string(taxonomy.get("code")),
        "address_street": address_street,
        "address_city": _normalize_optional_string(address.get("city")),
        "address_state": _normalize_optional_string(address.get("state")),
        "address_zip": _normalize_optional_string(address.get("postal_code")),
        "phone": _normalize_optional_string(address.get("telephone_number")),
    }


@router.get("/pecos-check")
def physician_pecos_check(
    npi: str,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    normalized_npi = _normalize_npi(npi)
    if not normalized_npi:
        return {"status": "unknown", "reason": "NPI is required"}

    cache_entry = db.query(PhysicianPecosCache).filter(PhysicianPecosCache.npi == normalized_npi).first()
    if cache_entry is None:
        return {
            "status": "unknown",
            "reason": "PECOS dataset cache not yet loaded",
            "npi": normalized_npi,
        }

    now = datetime.now(timezone.utc)
    (
        db.query(Physician)
        .filter(Physician.tenant_id == tenant_id, Physician.npi == normalized_npi)
        .update(
            {
                Physician.pecos_status: cache_entry.status,
                Physician.pecos_checked_at: now,
            },
            synchronize_session=False,
        )
    )
    db.commit()

    return {
        "status": cache_entry.status,
        "reason": cache_entry.reason,
        "source": cache_entry.source,
        "checked_at": cache_entry.checked_at,
        "refreshed_at": cache_entry.refreshed_at,
        "npi": normalized_npi,
    }


@router.post("")
def create_physician(
    payload: PhysicianWrite,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    actor_id = _actor_id(user)

    physician = Physician(
        tenant_id=tenant_id,
        created_by=actor_id,
        updated_by=actor_id,
        updated_at=datetime.now(timezone.utc),
    )
    _apply_physician_payload(physician, payload)
    db.add(physician)
    db.commit()
    db.refresh(physician)
    return _serialize_physician(physician)


@router.get("/{physician_id}")
def get_physician(
    physician_id: uuid.UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    physician = (
        db.query(Physician)
        .filter(Physician.id == physician_id, Physician.tenant_id == tenant_id)
        .first()
    )
    if physician is None:
        raise HTTPException(status_code=404, detail="Physician not found")
    return _serialize_physician(physician)


@router.put("/{physician_id}")
def update_physician(
    physician_id: uuid.UUID,
    payload: PhysicianWrite,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    actor_id = _actor_id(user)
    physician = (
        db.query(Physician)
        .filter(Physician.id == physician_id, Physician.tenant_id == tenant_id)
        .first()
    )
    if physician is None:
        raise HTTPException(status_code=404, detail="Physician not found")

    _apply_physician_payload(physician, payload)
    physician.updated_by = actor_id
    physician.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(physician)
    return _serialize_physician(physician)
