from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session


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
            pf.last_name

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
            payer_type
        FROM patient_payers
        WHERE patient_id = :patient_id
        ORDER BY id
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


def _build_patient_block(patient: dict) -> dict:
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


def _build_payer_block(payers: list[dict]) -> dict:
    primary = payers[0] if payers else None

    return {
        "primary_payer": primary,
        "all_payers": payers,
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
    cycle = _fetch_billing_cycle_row(db, billing_cycle_id)
    snapshot = _fetch_latest_snapshot_for_cycle(db, patient_id, billing_cycle_id)
    payers = _fetch_patient_payers(db, patient_id)

    claim_header = _build_claim_header(patient, cycle, snapshot)
    patient_block = _build_patient_block(patient)
    diagnosis_block = _build_diagnosis_block(patient)
    payer_block = _build_payer_block(payers)
    claim_lines = _build_claim_lines(snapshot)
    export_metadata = _build_export_metadata(snapshot)

    return {
        "claim_header": claim_header,
        "patient": patient_block,
        "diagnosis": diagnosis_block,
        "payer": payer_block,
        "claim_lines": claim_lines,
        "export_metadata": export_metadata,
    }