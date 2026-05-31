from __future__ import annotations

from datetime import datetime


class EDIBuilderError(RuntimeError):
    pass


# ---------------------------------------------------------
# SAFE HELPERS
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# MAIN BUILDER
# ---------------------------------------------------------

def build_837i_text(export_payload: dict) -> str:
    """
    Enterprise-safe 837I builder using Step 5/6 payload.
    """

    if not isinstance(export_payload, dict):
        raise EDIBuilderError("Invalid export payload")

    claim_header = export_payload.get("claim_header", {})
    patient = export_payload.get("patient", {})
    diagnosis = export_payload.get("diagnosis", {})
    payer = export_payload.get("payer", {})
    claim_lines = export_payload.get("claim_lines", [])

    if not claim_header:
        raise EDIBuilderError("Missing claim_header")
    if not patient:
        raise EDIBuilderError("Missing patient")

    # ---------------------------------------------------------
    # BASIC FIELDS
    # ---------------------------------------------------------

    claim_control_number = _clean(claim_header.get("claim_control_number"))
    total_amount = _clean(claim_header.get("total_estimated_amount", "0.00"))

    statement_from = _yyyymmdd(claim_header.get("statement_from_date"))
    statement_to = _yyyymmdd(claim_header.get("statement_to_date"))

    patient_name = _clean(patient.get("patient_name"))
    patient_id = _clean(patient.get("patient_id"))
    patient_mrn = _clean(patient.get("mrn"))
    patient_dob = _yyyymmdd(patient.get("date_of_birth"))

    primary_dx = _clean(diagnosis.get("primary_diagnosis"))

    primary_payer = payer.get("primary_payer") or {}
    payer_name = _clean(primary_payer.get("payer_name")) or "PRIMARY PAYER"

    # ---------------------------------------------------------
    # START SEGMENTS
    # ---------------------------------------------------------

    segments: list[str] = []

    # ISA
    segments.append(
        _segment(
            "ISA",
            "00", "", "00", "",
            "ZZ", "SNSHOSPICEEMR",
            "ZZ", "RECEIVER",
            _date_now(),
            _hhmm_now(),
            "^",
            "00501",
            "000000001",
            "0",
            "P",
            ":",
        )
    )

    # GS
    segments.append(
        _segment(
            "GS",
            "HC",
            "SNSHOSPICEEMR",
            "RECEIVER",
            datetime.utcnow().strftime("%Y%m%d"),
            _hhmm_now(),
            "1",
            "X",
            "005010X223A2",
        )
    )

    # ST + BHT
    segments.append(_segment("ST", "837", "0001", "005010X223A2"))
    segments.append(
        _segment(
            "BHT",
            "0019",
            "00",
            claim_control_number,
            datetime.utcnow().strftime("%Y%m%d"),
            _hhmm_now(),
            "CH",
        )
    )

    # Submitter + Receiver
    segments.append(_segment("NM1", "41", "2", "SNS HOSPICE EMR", "", "", "", "", "46", "SUBMITTER"))
    segments.append(_segment("PER", "IC", "BILLING", "TE", "0000000000"))
    segments.append(_segment("NM1", "40", "2", payer_name, "", "", "", "", "46", "RECEIVER"))

    # Billing Provider
    segments.append(_segment("HL", "1", "", "20", "1"))
    segments.append(_segment("PRV", "BI", "PXC", "251E00000X"))
    segments.append(_segment("NM1", "85", "2", "SNS HOSPICE EMR", "", "", "", "", "XX", "0000000000"))
    segments.append(_segment("N3", "123 BILLING PLACE"))
    segments.append(_segment("N4", "RANCHO CUCAMONGA", "CA", "91730"))
    segments.append(_segment("REF", "EI", "000000000"))

    # Patient HL
    segments.append(_segment("HL", "2", "1", "22", "0"))
    segments.append(_segment("SBR", "P", "18"))

    segments.append(
        _segment(
            "NM1",
            "IL",
            "1",
            patient_name,
            "",
            "",
            "",
            "",
            "MI",
            patient_mrn or patient_id,
        )
    )

    if patient_dob:
        segments.append(_segment("DMG", "D8", patient_dob))

    # Claim
    segments.append(
        _segment(
            "CLM",
            claim_control_number,
            total_amount,
            "",
            "",
            "11:B:1",
            "Y",
            "A",
            "Y",
            "I",
        )
    )

    if statement_from:
        segments.append(
            _segment(
                "DTP",
                "434",
                "RD8",
                f"{statement_from}-{statement_to or statement_from}",
            )
        )

    # Diagnosis
    if primary_dx:
        segments.append(_segment("HI", f"ABK:{primary_dx}"))

    # ---------------------------------------------------------
    # CLAIM LINES
    # ---------------------------------------------------------

    if not isinstance(claim_lines, list):
        raise EDIBuilderError("Invalid claim_lines")

    for idx, line in enumerate(claim_lines, start=1):
        revenue_code = _clean(line.get("revenue_code"))
        amount = _clean(line.get("estimated_amount"))
        days = _clean(line.get("days"))
        from_date = _yyyymmdd(line.get("from_date"))
        to_date = _yyyymmdd(line.get("to_date"))

        if not revenue_code:
            continue

        segments.append(_segment("LX", idx))
        segments.append(_segment("SV2", revenue_code, amount, "UN", days))

        if from_date:
            segments.append(
                _segment(
                    "DTP",
                    "472",
                    "RD8",
                    f"{from_date}-{to_date or from_date}",
                )
            )

    # ---------------------------------------------------------
    # END SEGMENTS
    # ---------------------------------------------------------

    segment_count = len(segments) + 1

    segments.append(_segment("SE", segment_count, "0001"))
    segments.append(_segment("GE", "1", "1"))
    segments.append(_segment("IEA", "1", "000000001"))

    return "\n".join(segments)
