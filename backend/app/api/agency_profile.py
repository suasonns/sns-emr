"""Agency (tenant) profile — tenant-scoped self-service settings.

Backs the "General" and "Clinical" tabs of Agency Settings with the real
identity/settings fields that exist on the `tenants` table. Per this
project's "never fabricate data" policy, only columns that actually exist
are returned; the frontend must not invent address/phone/administrator/
service-area/operating-hours values that have no backing schema.

Also exposes the agency's own operational defaults (Medical Director,
Facesheet Protection Mode) -- these are tenant governance decisions, never
values a hospital document or another tenant should determine.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator

from app.api.patients import get_db_with_request_state, require_tenant_user, _tenant_id_uuid
from app.core.permissions import require_roles
from app.models.physician import Physician
from app.models.tenant import Tenant

router = APIRouter(prefix="/agency-profile", tags=["agency-profile"])

VALID_FACESHEET_PROTECTION_MODES = {"OFF", "WARN", "REQUIRE_REVIEW"}

# Tenant-settings edit access mirrors the "Administrator / DPCS Access Only"
# gate already shown on the Agency Settings page.
AGENCY_SETTINGS_ADMIN_ROLES = ["DPCS_ADMINISTRATOR", "ADMINISTRATOR", "DPCS"]


def _serialize(tenant: Tenant, db) -> dict:
    default_md = None
    if tenant.default_medical_director_physician_id:
        physician = (
            db.query(Physician)
            .filter(
                Physician.id == tenant.default_medical_director_physician_id,
                Physician.tenant_id == tenant.id,
            )
            .first()
        )
        if physician is not None:
            default_md = {
                "physician_id": str(physician.id),
                "display_name": physician.display_name,
                "npi": physician.npi,
            }
        # If the FK points at a physician no longer in this tenant's
        # directory (should be impossible given the composite DB FK, but
        # defensive against a manual/legacy row), surface NOT_CONFIGURED
        # rather than fabricating a name.

    return {
        "tenant_id": str(tenant.id),
        "legal_name": tenant.legal_name,
        "display_name": tenant.display_name,
        "npi": tenant.npi,
        "ein": tenant.ein,
        "ptan": tenant.ptan,
        "tenant_type": tenant.tenant_type,
        "status": tenant.status,
        "cbsa_code": tenant.cbsa_code,
        "facesheet_protection_mode": tenant.facesheet_protection_mode,
        "default_medical_director": default_md,
    }


@router.get("")
def get_agency_profile(
    db=Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        return None
    return _serialize(tenant, db)


class AgencySettingsUpdate(BaseModel):
    facesheet_protection_mode: str | None = None
    # Explicit sentinel-free "clear the default" support: pass the string
    # "null" is NOT how this works -- omit the field to leave unchanged,
    # or pass an empty string to clear it back to NOT_CONFIGURED.
    default_medical_director_physician_id: str | None = None

    @field_validator("facesheet_protection_mode")
    @classmethod
    def _validate_mode(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in VALID_FACESHEET_PROTECTION_MODES:
            raise ValueError(
                f"facesheet_protection_mode must be one of {sorted(VALID_FACESHEET_PROTECTION_MODES)}"
            )
        return value


@router.patch("")
def update_agency_settings(
    payload: AgencySettingsUpdate,
    db=Depends(get_db_with_request_state),
    user=Depends(require_roles(AGENCY_SETTINGS_ADMIN_ROLES)),
):
    tenant_id = _tenant_id_uuid(user)
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    data = payload.model_dump(exclude_unset=True)

    if "facesheet_protection_mode" in data and data["facesheet_protection_mode"] is not None:
        tenant.facesheet_protection_mode = data["facesheet_protection_mode"]

    if "default_medical_director_physician_id" in data:
        raw_value = data["default_medical_director_physician_id"]
        if raw_value is None or raw_value == "":
            tenant.default_medical_director_physician_id = None
        else:
            try:
                physician_id = uuid.UUID(str(raw_value))
            except (ValueError, AttributeError, TypeError):
                raise HTTPException(status_code=400, detail="Invalid physician_id")

            # Never allow a tenant default to point at another tenant's
            # physician record -- this is enforced again at the DB level
            # by the composite foreign key, but reject early with a clear
            # error rather than a raw constraint-violation 500.
            physician = (
                db.query(Physician)
                .filter(Physician.id == physician_id, Physician.tenant_id == tenant_id)
                .first()
            )
            if physician is None:
                raise HTTPException(
                    status_code=400,
                    detail="Physician not found in this tenant's directory",
                )
            tenant.default_medical_director_physician_id = physician_id

    db.commit()
    db.refresh(tenant)
    return _serialize(tenant, db)
