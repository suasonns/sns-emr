from __future__ import annotations

"""
Builds the real patient/provider/payer data blocks needed for a hospice
NOE/NOTR electronic notice (837 TOB 8XA/8XB) -- the same real identity
sources used for the actual 837I claim export (claim_export_service),
minus anything claim/revenue-specific (NOE/NOTR carries no charges).
"""

from datetime import date

from sqlalchemy.orm import Session

from app.billing.services.claim_export_service import (
    ClaimExportError,
    _build_attending_provider_block,
    _build_patient_block,
    _build_payer_block,
    _build_provider_block,
    _fetch_patient_payers,
    _fetch_patient_row,
    _fetch_tenant_row,
)
from app.billing.services.msp_validation_service import resolve_payer_sequence


def build_notice_export(
    db: Session,
    patient_id: str,
    *,
    effective_date: date,
) -> dict:
    """
    Real patient/provider/attending/payer blocks for a NOE or NOTR 837
    notice, evaluated as of `effective_date` (the election or discharge/
    revocation effective date) -- never today's date, since payer
    coverage must be evaluated at the notice's real effective date.
    """
    patient = _fetch_patient_row(db, patient_id)
    tenant = _fetch_tenant_row(db, patient["tenant_id"])
    payers = _fetch_patient_payers(db, patient_id)

    sequence = resolve_payer_sequence(payers, service_date=effective_date)
    if sequence.has_conflict:
        raise ClaimExportError(
            f"Cannot generate notice -- payer sequence is ambiguous: {sequence.conflict_reason}"
        )

    payer_block = _build_payer_block(sequence)
    primary_payer = payer_block["primary_payer"]

    return {
        "patient": _build_patient_block(patient, primary_payer),
        "provider": _build_provider_block(tenant),
        "attending_provider": _build_attending_provider_block(patient),
        "payer": payer_block,
        "tenant_id": patient["tenant_id"],
    }
