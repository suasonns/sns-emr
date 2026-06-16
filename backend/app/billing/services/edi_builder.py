from __future__ import annotations

import json
import os
from datetime import datetime
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session


class EDIBuilderError(RuntimeError):
    pass


# =========================================================
# CONSTANTS
# =========================================================

ALLOWED_HOSPICE_REV_CODES = {
    "0651",  # Routine Home Care
    "0652",  # Continuous Home Care
    "0655",  # Inpatient Respite
    "0656",  # General Inpatient Care
}


# =========================================================
# HELPERS
# =========================================================

def _clean(value) -> str:
    if value is None:
        return ""
    return str(value).replace("~", "").replace("*", "").replace(":", "").strip()


def _yyyymmdd(value: str | None) -> str:
    if not value:
        return ""
    return value.replace("-", "")


def _hhmm_now() -> str:
    return datetime.utcnow().strftime("%H%M")


def _date_now() -> str:
    return datetime.utcnow().strftime("%y%m%d")


def _segment(*elements: object) -> str:
    return "*".join(_clean(x) for x in elements) + "~"


# =========================================================
# VALIDATION
# =========================================================

def _validate_claim_identity(payer_type, subscriber_id, subscriber_id_type):
    if not subscriber_id:
        raise EDIBuilderError("Missing subscriber_id")

    if payer_type == "MEDICARE" and subscriber_id_type != "MBI":
        raise EDIBuilderError("Medicare requires MBI")


def _validate_provider_identity(npi, tax_id):
    if not npi or len(npi) != 10:
        raise EDIBuilderError("Invalid billing provider NPI")

    if not tax_id or len(tax_id) < 9:
        raise EDIBuilderError("Invalid billing provider EIN")


def _validate_attending(att):
    if not att.get("first_name") or not att.get("last_name"):
        raise EDIBuilderError("Missing attending provider name")

    if not att.get("npi") or len(att["npi"]) != 10:
        raise EDIBuilderError("Invalid attending provider NPI")


def _validate_optional_provider(p, label):
    if any(p.values()):
        if not all(p.values()):
            raise EDIBuilderError(f"Incomplete {label} provider")

        if len(p["npi"]) != 10:
            raise EDIBuilderError(f"Invalid {label} NPI")


def _validate_hospice_lines(lines):
    if not isinstance(lines, list):
        raise EDIBuilderError("Invalid claim_lines")

    for row in lines:
        code = _clean(row.get("revenue_code"))
        if code not in ALLOWED_HOSPICE_REV_CODES:
            raise EDIBuilderError(f"Invalid hospice revenue code: {code}")


# =========================================================
# MAIN BUILDER
# =========================================================

def build_837i_text(export_payload: dict) -> str:

    claim_header = export_payload.get("claim_header", {})
    patient = export_payload.get("patient", {})
    diagnosis = export_payload.get("diagnosis", {})
    payer = export_payload.get("payer", {})
    provider = export_payload.get("provider", {})
    attending = export_payload.get("attending_provider", {})
    rendering = export_payload.get("rendering_provider", {})
    certifying = export_payload.get("certifying_provider", {})
    claim_lines = export_payload.get("claim_lines", [])

    if not claim_header or not patient or not provider or not attending:
        raise EDIBuilderError("Missing required payload sections")

    # ---------------------------------------------------------
    # VALUES
    # ---------------------------------------------------------
    claim_control_number = _clean(claim_header.get("claim_control_number"))
    total_amount = _clean(claim_header.get("total_estimated_amount", "0.00"))

    patient_name = _clean(patient.get("patient_name"))
    patient_dob = _yyyymmdd(patient.get("date_of_birth"))

    subscriber_id = _clean(patient.get("subscriber_id"))
    subscriber_id_type = _clean(patient.get("subscriber_id_type")) or "MI"

    payer_obj = payer.get("primary_payer", {})
    payer_name = _clean(payer_obj.get("payer_name"))
    payer_type = _clean(payer_obj.get("payer_type"))

    provider_name = _clean(provider.get("agency_name"))
    provider_npi = _clean(provider.get("npi"))
    provider_tax_id = _clean(provider.get("tax_id"))

    primary_dx = _clean(diagnosis.get("primary_diagnosis"))

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------
    _validate_claim_identity(payer_type, subscriber_id, subscriber_id_type)
    _validate_provider_identity(provider_npi, provider_tax_id)
    _validate_attending(attending)
    _validate_optional_provider(rendering, "Rendering")
    _validate_optional_provider(certifying, "Certifying")
    _validate_hospice_lines(claim_lines)

    # ---------------------------------------------------------
    # BUILD SEGMENTS
    # ---------------------------------------------------------
    segments: list[str] = []

    segments.append(_segment("ISA", "00", "", "00", "", "ZZ", "SNSHOSPICEEMR", "ZZ", "RECEIVER", _date_now(), _hhmm_now(), "^", "00501", "000000001", "0", "P", ":"))
    segments.append(_segment("GS", "HC", "SNSHOSPICEEMR", "RECEIVER", datetime.utcnow().strftime("%Y%m%d"), _hhmm_now(), "1", "X", "005010X223A2"))
    segments.append(_segment("ST", "837", "0001", "005010X223A2"))
    segments.append(_segment("BHT", "0019", "00", claim_control_number, datetime.utcnow().strftime("%Y%m%d"), _hhmm_now(), "CH"))

    # SUBMITTER / RECEIVER
    segments.append(_segment("NM1", "41", "2", provider_name, "", "", "", "", "46", "SUBMITTER"))
    segments.append(_segment("PER", "IC", "BILLING", "TE", "0000000000"))
    segments.append(_segment("NM1", "40", "2", payer_name, "", "", "", "", "46", "RECEIVER"))

    # BILLING PROVIDER
    segments.append(_segment("HL", "1", "", "20", "1"))
    segments.append(_segment("PRV", "BI", "PXC", "251G00000X"))
    segments.append(_segment("NM1", "85", "2", provider_name, "", "", "", "", "XX", provider_npi))
    segments.append(_segment("N3", "123 BILLING PLACE"))
    segments.append(_segment("N4", "RANCHO CUCAMONGA", "CA", "91730"))
    segments.append(_segment("REF", "EI", provider_tax_id))

    # PATIENT
    segments.append(_segment("HL", "2", "1", "22", "0"))
    segments.append(_segment("SBR", "P", "18"))
    segments.append(_segment("NM1", "IL", "1", patient_name, "", "", "", "", subscriber_id_type, subscriber_id))
    if patient_dob:
        segments.append(_segment("DMG", "D8", patient_dob))

    # CLAIM
    segments.append(_segment("CLM", claim_control_number, total_amount, "", "", "11:B:1", "Y", "A", "Y", "I"))

    # DIAGNOSIS
    if primary_dx:
        segments.append(_segment("HI", f"ABK:{primary_dx}"))

    # ATTENDING (REQUIRED)
    segments.append(_segment("NM1", "71", "1", attending["last_name"], attending["first_name"], "", "", "", "XX", attending["npi"]))

    # RENDERING
    if rendering.get("npi"):
        segments.append(_segment("NM1", "82", "1", rendering["last_name"], rendering["first_name"], "", "", "", "XX", rendering["npi"]))

    # CERTIFYING
    if certifying.get("npi"):
        segments.append(_segment("NM1", "DN", "1", certifying["last_name"], certifying["first_name"], "", "", "", "XX", certifying["npi"]))

    # LINES
    for i, line in enumerate(claim_lines, start=1):
        segments.append(_segment("LX", i))
        segments.append(_segment("SV2", line.get("revenue_code"), line.get("estimated_amount"), "UN", line.get("days")))

    segments.append(_segment("SE", len(segments) + 1, "0001"))
    segments.append(_segment("GE", "1", "1"))
    segments.append(_segment("IEA", "1", "000000001"))

    return "\n".join(segments)

# =========================================================
# FILE EXPORT + AUDIT LOGGING
# =========================================================

def save_edi_to_file(
    db,
    edi_text: str,
    export_payload: dict,
    base_dir: str = "app/billing/exports/claims",
) -> str:
    """
    ✅ Saves EDI file to structured tenant directory

    Structure:
    /exports/{tenant_id}/{YYYY-MM}/file.edi
    """

    if not edi_text:
        raise EDIBuilderError("Empty EDI text")

    if not isinstance(export_payload, dict):
        raise EDIBuilderError("Invalid export_payload")

    now = datetime.utcnow()

    claim_header = export_payload.get("claim_header", {})
    patient = export_payload.get("patient", {})
    tenant_id = claim_header.get("tenant_id")

    if not tenant_id:
        raise EDIBuilderError("Missing tenant_id")

    tenant_id = _clean(tenant_id)
    month_folder = now.strftime("%Y-%m")

    full_dir = os.path.join(base_dir, tenant_id, month_folder)
    os.makedirs(full_dir, exist_ok=True)

    patient_id = _clean(patient.get("patient_id", "unknown"))
    billing_cycle_id = _clean(claim_header.get("billing_cycle_id", "unknown"))

    filename = (
        f"837I_{patient_id}_{billing_cycle_id}_{now.strftime('%Y%m%d_%H%M%S')}.edi"
    )

    file_path = os.path.join(full_dir, filename)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(edi_text)
    except Exception as e:
        raise EDIBuilderError(f"Failed to write EDI file: {e}") from e

    return file_path
