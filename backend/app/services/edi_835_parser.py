from __future__ import annotations

from typing import Any


class EDI835ParseError(RuntimeError):
    pass


def _to_decimal(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_835_file(raw_text: str) -> dict[str, Any]:
    """
    Parses an X12 835 (Health Care Claim Payment/Advice) EDI file into a
    structured dict: batch-level payer/payment info plus one entry per
    CLP (claim payment) segment, each carrying its CAS (claim adjustment
    -- including denial/CARC) segments.

    This is a pragmatic, targeted 835 parser -- it extracts only the
    fields this app uses for payment posting and denial tracking (BPR,
    N1*PR, CLP, CAS, NM1*QC, REF*1K/REF*6R, DTM), not a full X12 835
    implementation. Segment terminator is assumed to be "~" and element
    separator "*", matching the 837I builder used elsewhere in this app
    (see app.billing.services.edi_builder).
    """
    if not raw_text or not raw_text.strip():
        raise EDI835ParseError("Empty 835 file")

    segments = [
        seg.strip()
        for seg in raw_text.replace("\r", "").replace("\n", "").split("~")
        if seg.strip()
    ]

    batch_payer_name: str | None = None
    batch_total_paid: float | None = None
    batch_payment_date: str | None = None

    claims: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for segment in segments:
        elements = segment.split("*")
        seg_id = elements[0]

        if seg_id == "BPR":
            # BPR02 = total actual provider payment amount
            # BPR16 = payment effective/settlement date (CCYYMMDD)
            if len(elements) > 2:
                batch_total_paid = _to_decimal(elements[2])
            if len(elements) > 16 and elements[16]:
                batch_payment_date = elements[16]

        elif seg_id == "N1" and len(elements) > 2 and elements[1] == "PR":
            # N1*PR*<payer name> -- payer identification loop
            batch_payer_name = elements[2] or None

        elif seg_id == "CLP":
            if current is not None:
                claims.append(current)
            current = {
                "claim_control_number": elements[1] if len(elements) > 1 else None,
                "claim_status_code": elements[2] if len(elements) > 2 else None,
                "billed_amount": _to_decimal(elements[3]) if len(elements) > 3 else None,
                "paid_amount": _to_decimal(elements[4]) if len(elements) > 4 else None,
                "patient_responsibility": _to_decimal(elements[5]) if len(elements) > 5 else None,
                "payer_claim_control_number": elements[7] if len(elements) > 7 else None,
                "patient_name": None,
                "payment_date": None,
                "adjustments": [],
            }

        elif (
            seg_id == "NM1"
            and current is not None
            and len(elements) > 1
            and elements[1] == "QC"
        ):
            # NM1*QC*1*<last>*<first> -- patient (subscriber/claimant) name
            last = elements[3] if len(elements) > 3 else ""
            first = elements[4] if len(elements) > 4 else ""
            current["patient_name"] = f"{last}, {first}".strip(", ") or None

        elif (
            seg_id == "REF"
            and current is not None
            and len(elements) > 2
            and elements[1] in ("1K", "6R")
        ):
            current["payer_claim_control_number"] = elements[2]

        elif seg_id == "DTM" and current is not None and len(elements) > 2:
            # DTM*232 statement-from, *233 statement-to, *036 expiration --
            # any of these is a reasonable payment-date fallback if BPR16
            # is missing from a truncated test file.
            if elements[1] in ("232", "233", "036", "405") and not current["payment_date"]:
                current["payment_date"] = elements[2]

        elif seg_id == "CAS" and current is not None:
            # CAS*<group_code>*<carc>*<amount>*<qty> -- repeats in groups
            # of (carc, amount, qty) after the group code.
            group_code = elements[1] if len(elements) > 1 else None
            idx = 2
            while idx < len(elements) and elements[idx]:
                carc_code = elements[idx]
                amount = _to_decimal(elements[idx + 1]) if idx + 1 < len(elements) else None
                current["adjustments"].append(
                    {
                        "group_code": group_code,
                        "carc_code": carc_code,
                        "amount": amount,
                    }
                )
                idx += 3  # carc, amount, quantity (quantity usually omitted)

    if current is not None:
        claims.append(current)

    if not claims:
        raise EDI835ParseError("No CLP (claim payment) segments found in 835 file")

    return {
        "payer_name": batch_payer_name,
        "total_paid_amount": batch_total_paid,
        "payment_date": batch_payment_date,
        "claims": claims,
    }