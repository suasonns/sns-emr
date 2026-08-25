from __future__ import annotations

from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.billing.services.msp_validation_service import (
    build_msp_value_codes_for_claim,
    resolve_payer_sequence,
)


class ClaimExportError(RuntimeError):
    pass


def _fetch_patient_row(db: Session, patient_id: str) -> dict:
    sql = text(
        """
        SELECT
            p.id::text AS id,
            p.tenant_id::text AS tenant_id,
            p.mrn,
            p.date_of_birth,
            p.primary_diagnosis,

            -- SSOT NAME SOURCE
            pf.first_name,
            pf.middle_name,
            pf.last_name,

            -- attending provider (real, chart-of-record source)
            pf.attending_physician_name,
            pf.attending_physician_npi

        FROM patients p
        LEFT JOIN patient_facesheet pf
            ON pf.patient_id = p.id

        WHERE p.id::text = :patient_id
        LIMIT 1
        """
    )

    row = db.execute(sql, {"patient_id": patient_id}).mappings().first()
    if not row:
        raise ClaimExportError(f"Patient not found: {patient_id}")

    return dict(row)


def _fetch_tenant_row(db: Session, tenant_id: str) -> dict:
    sql = text(
        """
        SELECT
            id::text AS id,
            legal_name,
            display_name,
            npi,
            ein,
            ptan
        FROM tenants
        WHERE id::text = :tenant_id
        LIMIT 1
        """
    )

    row = db.execute(sql, {"tenant_id": tenant_id}).mappings().first()
    if not row:
        raise ClaimExportError(f"Tenant not found: {tenant_id}")

    return dict(row)


def _fetch_billing_cycle_row(db: Session, billing_cycle_id: str) -> dict:
    sql = text(
        """
        SELECT
            id,
            tenant_id,
            month,
            year,
            start_date,
            end_date
        FROM billing_cycles
        WHERE id = :billing_cycle_id
        LIMIT 1
        """
    )

    row = db.execute(sql, {"billing_cycle_id": billing_cycle_id}).mappings().first()
    if not row:
        raise ClaimExportError(f"Billing cycle not found: {billing_cycle_id}")

    return dict(row)


def _fetch_latest_snapshot_for_cycle(
    db: Session,
    patient_id: str,
    billing_cycle_id: str,
) -> dict:
    sql = text(
        """
        SELECT data
        FROM billing_snapshots
        WHERE patient_id = :patient_id
          AND data ->> 'billing_cycle_id' = :billing_cycle_id
        ORDER BY id DESC
        LIMIT 1
        """
    )

    row = db.execute(
        sql,
        {
            "patient_id": patient_id,
            "billing_cycle_id": billing_cycle_id,
        },
    ).mappings().first()

    if not row:
        raise ClaimExportError(
            f"No billing snapshot found for patient {patient_id} and cycle {billing_cycle_id}"
        )

    return row["data"]


def _fetch_patient_payers(db: Session, patient_id: str) -> list[dict]:
    sql = text(
        """
        SELECT
            id,
            patient_id,
            payer_name,
            payer_type,
            subscriber_id,
            subscriber_id_type,
            is_primary,
            effective_start_date,
            end_date,
            msp_type_code,
            priority_order
        FROM patient_payers
        WHERE patient_id = :patient_id
        ORDER BY is_primary DESC, id
        """
    )
    rows = db.execute(sql, {"patient_id": patient_id}).mappings().all()
    return [dict(r) for r in rows]


def _build_patient_name(first_name, middle_name, last_name) -> str | None:
    if not first_name and not last_name:
        return None

    middle_initial = middle_name[0] if middle_name else None

    if middle_initial:
        return f"{last_name}, {first_name} {middle_initial}"

    return f"{last_name}, {first_name}"


def _split_person_name(full_name: str | None) -> tuple[str | None, str | None]:
    """
    Splits a free-text "First Last" or "First Last, MD" name into
    (first_name, last_name) for EDI NM1 segments. Strips a trailing
    credential (", MD", ", DO", etc.) if present.
    """
    if not full_name:
        return None, None

    name = full_name.split(",")[0].strip()
    parts = name.split()
    if not parts:
        return None, None
    if len(parts) == 1:
        return parts[0], None

    return parts[0], parts[-1]


def _build_claim_header(patient: dict, cycle: dict, snapshot: dict) -> dict:
    billing_period = snapshot.get("billing_period", {})
    revenue_summary = snapshot.get("revenue_summary", {})

    return {
        "claim_control_number": str(uuid4()),
        "claim_type": "INSTITUTIONAL_HOSPICE",
        "claim_frequency_code": "1",
        "statement_from_date": billing_period.get("start_date"),
        "statement_to_date": billing_period.get("end_date"),
        "billing_cycle_id": cycle["id"],
        "total_estimated_amount": revenue_summary.get("total_estimated_amount", "0.00"),
        "generated_at_utc": datetime.utcnow().isoformat(),
        "tenant_id": patient.get("tenant_id"),
    }


def _build_patient_block(patient: dict, primary_payer: dict | None) -> dict:
    patient_name = _build_patient_name(
        patient.get("first_name"),
        patient.get("middle_name"),
        patient.get("last_name"),
    )

    return {
        "patient_id": patient.get("id"),
        "patient_name": patient_name,
        "mrn": patient.get("mrn"),
        "date_of_birth": (
            str(patient["date_of_birth"]) if patient.get("date_of_birth") else None
        ),
        # Required by build_837i_text's subscriber (NM1*IL) segment --
        # sourced from the patient's *resolved* primary payer (real MSP
        # sequencing), never a naive payers[0] pick.
        "subscriber_id": (primary_payer or {}).get("subscriber_id"),
        "subscriber_id_type": (primary_payer or {}).get("subscriber_id_type"),
    }


def _build_provider_block(tenant: dict) -> dict:
    """
    Billing/facility provider -- the hospice agency itself. Real identifiers
    (NPI/EIN/agency name) come from the tenant record, never fabricated.
    """
    return {
        "agency_name": tenant.get("legal_name") or tenant.get("display_name"),
        "npi": tenant.get("npi"),
        "tax_id": tenant.get("ein"),
        "ptan": tenant.get("ptan"),
    }


def _build_attending_provider_block(patient: dict) -> dict:
    """
    Attending/certifying hospice physician -- sourced from the patient's
    real facesheet record (attending_physician_name/npi), never fabricated.
    """
    first_name, last_name = _split_person_name(patient.get("attending_physician_name"))

    return {
        "first_name": first_name,
        "last_name": last_name,
        "npi": patient.get("attending_physician_npi"),
    }


def _build_diagnosis_block(patient: dict) -> dict:
    primary_dx = patient.get("primary_diagnosis")

    return {
        "primary_diagnosis": primary_dx,
        "hi_segments": [
            {
                "qualifier": "ABK",
                "diagnosis_code": primary_dx,
            }
        ]
        if primary_dx
        else [],
    }


def _build_payer_block(sequence) -> dict:
    """
    Builds the claim's payer block from a resolved MspSequenceResult
    (see app.billing.services.msp_validation_service). The primary payer
    and full sequence come from real MSP-aware ordering, never a naive
    payers[0]/is_primary pick.
    """
    resolved = [
        {
            "payer_id": p.payer_id,
            "payer_name": p.payer_name,
            "payer_type": p.payer_type,
            "subscriber_id": p.subscriber_id,
            "subscriber_id_type": p.subscriber_id_type,
            "msp_type_code": p.msp_type_code,
            "sequence_code": p.sequence_code,
            "priority_order": p.priority_order,
        }
        for p in sequence.payers
    ]

    primary = resolved[0] if resolved else None

    return {
        "primary_payer": primary,
        "all_payers": resolved,
        "msp_value_codes": build_msp_value_codes_for_claim(sequence),
    }


def _build_claim_lines(snapshot: dict) -> list[dict]:
    raw_lines = snapshot.get("claim_lines", [])
    result: list[dict] = []
    for idx, line in enumerate(raw_lines, start=1):
        result.append(
            {
                "line_number": idx,
                "revenue_code": line.get("revenue_code"),
                "from_date": line.get("from_date"),
                "to_date": line.get("to_date"),
                "days_or_units": line.get("days"),
                "loc": line.get("loc"),
                "pos": line.get("pos"),
                "facility_name": line.get("facility_name"),
                "rate": line.get("rate"),
                "estimated_amount": line.get("estimated_amount"),
                # Must survive into the export payload -- edi_builder relies
                # on this to refuse generating an 837I for a claim line that
                # is a known, unpriced rate gap (not an intentional $0.00).
                "rate_gap_reason": line.get("rate_gap_reason"),
                # A late-NOE penalty is an intentional, CMS-mandated $0.00
                # (not a gap needing resolution) -- carried through so the
                # export/EDI output is auditable, but does NOT block export.
                "noe_penalty_reason": line.get("noe_penalty_reason"),
            }
        )

    return result


def _build_export_metadata(snapshot: dict) -> dict:
    return {
        "format": "837_READY_JSON",
        "version": "v1",
        "status": snapshot.get("status"),
        "risk_score": snapshot.get("risk_score"),
        "units": snapshot.get("units", {}),
        "loc_summary": snapshot.get("loc_summary", {}),
        "rate_schedule_used": snapshot.get("rate_schedule_used", {}),
    }


def build_patient_claim_export(
    db: Session,
    patient_id: str,
    billing_cycle_id: str,
) -> dict:
    patient = _fetch_patient_row(db, patient_id)
    tenant = _fetch_tenant_row(db, patient["tenant_id"])
    cycle = _fetch_billing_cycle_row(db, billing_cycle_id)
    snapshot = _fetch_latest_snapshot_for_cycle(db, patient_id, billing_cycle_id)
    payers = _fetch_patient_payers(db, patient_id)

    service_date = _resolve_service_date(snapshot, cycle)
    sequence = resolve_payer_sequence(payers, service_date=service_date)
    if sequence.has_conflict:
        raise ClaimExportError(
            f"Cannot export claim -- payer sequence is ambiguous: {sequence.conflict_reason}"
        )

    payer_block = _build_payer_block(sequence)
    primary_payer = payer_block["primary_payer"]

    claim_header = _build_claim_header(patient, cycle, snapshot)
    patient_block = _build_patient_block(patient, primary_payer)
    diagnosis_block = _build_diagnosis_block(patient)
    provider_block = _build_provider_block(tenant)
    attending_provider_block = _build_attending_provider_block(patient)
    claim_lines = _build_claim_lines(snapshot)
    export_metadata = _build_export_metadata(snapshot)

    return {
        "claim_header": claim_header,
        "patient": patient_block,
        "diagnosis": diagnosis_block,
        "payer": payer_block,
        "provider": provider_block,
        "attending_provider": attending_provider_block,
        "claim_lines": claim_lines,
        "export_metadata": export_metadata,
    }


def _resolve_service_date(snapshot: dict, cycle: dict) -> date:
    """
    The date used to evaluate which payers are active/MSP for this claim.
    Prefer the billing period's real start date (from the snapshot), fall
    back to the billing cycle's start date -- never today's date, since
    that would evaluate coverage against the wrong point in time for
    claims generated after the fact.
    """
    billing_period = snapshot.get("billing_period", {}) if isinstance(snapshot, dict) else {}
    raw = billing_period.get("start_date") or cycle.get("start_date")
    if isinstance(raw, date):
        return raw
    if isinstance(raw, str):
        return date.fromisoformat(raw[:10])
    raise ClaimExportError("Cannot resolve a service date to evaluate payer sequence")