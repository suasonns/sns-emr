from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.patients import get_db_with_request_state, require_tenant_user, _tenant_id_uuid
from app.models.vendor import Vendor

router = APIRouter(prefix="/vendors", tags=["vendors"])

VALID_VENDOR_TYPES = {"Pharmacy", "DME", "Laboratory", "AL", "Contracted Staff", "Other"}
VALID_VENDOR_STATUSES = {"active", "inactive"}
VALID_LIST_STATUSES = {"active", "inactive", "both"}

CENSUS_GEOCODER_URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"



class VendorWrite(BaseModel):
    vendor_type: str
    name: str
    ncpdp_id: str | None = None
    address_street: str | None = None
    address_city: str | None = None
    address_state: str | None = None
    address_zip: str | None = None
    phone: str | None = None
    fax: str | None = None
    email: str | None = None
    contact_person: str | None = None
    npi: str | None = None
    npi_exp_date: datetime | None = None
    rx_state_lic: str | None = None
    rx_state_lic_exp_date: datetime | None = None
    bus_lic: str | None = None
    bus_lic_exp_date: datetime | None = None
    insurance: str | None = None
    insurance_exp_date: datetime | None = None
    note: str | None = None
    status: str = "active"


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


def _serialize_vendor(vendor: Vendor) -> dict[str, Any]:
    return {
        "id": str(vendor.id),
        "tenant_id": str(vendor.tenant_id),
        "vendor_type": vendor.vendor_type,
        "name": vendor.name,
        "ncpdp_id": vendor.ncpdp_id,
        "address_street": vendor.address_street,
        "address_city": vendor.address_city,
        "address_state": vendor.address_state,
        "address_zip": vendor.address_zip,
        "phone": vendor.phone,
        "fax": vendor.fax,
        "email": vendor.email,
        "contact_person": vendor.contact_person,
        "npi": vendor.npi,
        "npi_exp_date": vendor.npi_exp_date,
        "rx_state_lic": vendor.rx_state_lic,
        "rx_state_lic_exp_date": vendor.rx_state_lic_exp_date,
        "bus_lic": vendor.bus_lic,
        "bus_lic_exp_date": vendor.bus_lic_exp_date,
        "insurance": vendor.insurance,
        "insurance_exp_date": vendor.insurance_exp_date,
        "note": vendor.note,
        "status": vendor.status,
        "created_at": vendor.created_at,
        "created_by": str(vendor.created_by) if vendor.created_by else None,
        "updated_at": vendor.updated_at,
        "updated_by": str(vendor.updated_by) if vendor.updated_by else None,
    }


def _apply_vendor_payload(vendor: Vendor, payload: VendorWrite) -> None:
    normalized_type = _normalize_optional_string(payload.vendor_type)
    if not normalized_type or normalized_type not in VALID_VENDOR_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid vendor type. Must be one of: {sorted(VALID_VENDOR_TYPES)}")
    vendor.vendor_type = normalized_type

    normalized_name = _normalize_optional_string(payload.name)
    if not normalized_name:
        raise HTTPException(status_code=400, detail="Vendor name is required")
    vendor.name = normalized_name

    vendor.ncpdp_id = _normalize_optional_string(payload.ncpdp_id)
    vendor.address_street = _normalize_optional_string(payload.address_street)
    vendor.address_city = _normalize_optional_string(payload.address_city)
    vendor.address_state = _normalize_optional_string(payload.address_state)
    vendor.address_zip = _normalize_optional_string(payload.address_zip)
    vendor.phone = _normalize_optional_string(payload.phone)
    vendor.fax = _normalize_optional_string(payload.fax)
    vendor.email = _normalize_optional_string(payload.email)
    vendor.contact_person = _normalize_optional_string(payload.contact_person)
    vendor.npi = _normalize_npi(payload.npi)
    vendor.npi_exp_date = payload.npi_exp_date
    vendor.rx_state_lic = _normalize_optional_string(payload.rx_state_lic)
    vendor.rx_state_lic_exp_date = payload.rx_state_lic_exp_date
    vendor.bus_lic = _normalize_optional_string(payload.bus_lic)
    vendor.bus_lic_exp_date = payload.bus_lic_exp_date
    vendor.insurance = _normalize_optional_string(payload.insurance)
    vendor.insurance_exp_date = payload.insurance_exp_date
    vendor.note = _normalize_optional_string(payload.note)

    normalized_status = (_normalize_optional_string(payload.status) or "active").lower()
    if normalized_status not in VALID_VENDOR_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid vendor status")
    vendor.status = normalized_status


@router.get("")
def list_vendors(
    status: str = Query("active"),
    vendor_type: str | None = Query(default=None),
    name: str | None = Query(default=None),
    address: str | None = Query(default=None),
    npi: str | None = Query(default=None),
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    normalized_status = (status or "active").strip().lower()
    if normalized_status not in VALID_LIST_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status filter")

    query = db.query(Vendor).filter(Vendor.tenant_id == tenant_id)

    if normalized_status != "both":
        query = query.filter(Vendor.status == normalized_status)

    normalized_type = _normalize_optional_string(vendor_type)
    if normalized_type:
        query = query.filter(Vendor.vendor_type == normalized_type)

    normalized_name = _normalize_optional_string(name)
    if normalized_name:
        query = query.filter(Vendor.name.ilike(f"%{normalized_name}%"))

    normalized_address = _normalize_optional_string(address)
    if normalized_address:
        query = query.filter(
            or_(
                Vendor.address_street.ilike(f"%{normalized_address}%"),
                Vendor.address_city.ilike(f"%{normalized_address}%"),
                Vendor.address_state.ilike(f"%{normalized_address}%"),
                Vendor.address_zip.ilike(f"%{normalized_address}%"),
            )
        )

    normalized_npi = _normalize_optional_string(npi)
    if normalized_npi:
        query = query.filter(Vendor.npi.ilike(f"%{normalized_npi}%"))

    vendors = query.order_by(Vendor.name.asc()).all()
    return [_serialize_vendor(vendor) for vendor in vendors]


@router.post("")
def create_vendor(
    payload: VendorWrite,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    actor_id = _actor_id(user)

    vendor = Vendor(
        tenant_id=tenant_id,
        created_by=actor_id,
        updated_by=actor_id,
        updated_at=datetime.now(timezone.utc),
    )
    _apply_vendor_payload(vendor, payload)
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return _serialize_vendor(vendor)


@router.get("/address-lookup")
def address_lookup(
    query: str = Query(..., min_length=6),
    user=Depends(require_tenant_user),
):
    """Normalize/auto-complete a US street address via the free Census Bureau geocoder.

    Fails soft (returns found: False) on any error so it never blocks manual entry.
    """
    try:
        with httpx.Client(timeout=6.0) as client:
            response = client.get(
                CENSUS_GEOCODER_URL,
                params={"address": query, "benchmark": "Public_AR_Current", "format": "json"},
            )
            response.raise_for_status()
            payload = response.json()
    except Exception:
        return {"found": False}

    matches = (payload.get("result") or {}).get("addressMatches") or []
    if not matches:
        return {"found": False}

    match = matches[0]
    components = match.get("addressComponents") or {}
    street_parts = [
        str(components.get("preDirection") or "").strip(),
        str(components.get("preType") or "").strip(),
        str(components.get("streetName") or "").strip(),
        str(components.get("suffixType") or "").strip(),
        str(components.get("suffixDirection") or "").strip(),
    ]
    street = " ".join(part for part in street_parts if part)

    return {
        "found": True,
        "matched_address": match.get("matchedAddress"),
        "address_street": street or None,
        "address_city": _normalize_optional_string(components.get("city")),
        "address_state": _normalize_optional_string(components.get("state")),
        "address_zip": _normalize_optional_string(components.get("zip")),
    }


@router.get("/{vendor_id}")
def get_vendor(
    vendor_id: uuid.UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    vendor = (
        db.query(Vendor)
        .filter(Vendor.id == vendor_id, Vendor.tenant_id == tenant_id)
        .first()
    )
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return _serialize_vendor(vendor)


@router.put("/{vendor_id}")
def update_vendor(
    vendor_id: uuid.UUID,
    payload: VendorWrite,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    actor_id = _actor_id(user)
    vendor = (
        db.query(Vendor)
        .filter(Vendor.id == vendor_id, Vendor.tenant_id == tenant_id)
        .first()
    )
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")

    _apply_vendor_payload(vendor, payload)
    vendor.updated_by = actor_id
    vendor.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(vendor)
    return _serialize_vendor(vendor)


@router.delete("/{vendor_id}")
def delete_vendor(
    vendor_id: uuid.UUID,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    vendor = (
        db.query(Vendor)
        .filter(Vendor.id == vendor_id, Vendor.tenant_id == tenant_id)
        .first()
    )
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")

    vendor.status = "inactive"
    vendor.updated_by = _actor_id(user)
    vendor.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"deleted": True, "id": str(vendor_id)}
