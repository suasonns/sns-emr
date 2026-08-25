from __future__ import annotations

"""
Real electronic Notice of Election (NOE, TOB 81A) / Notice of Termination
or Revocation (NOTR, TOB 81B) 837I builder.

CMS requires the NOE to be filed within 5 calendar days of the hospice
election effective date, and the NOTR within 5 calendar days of a
discharge/revocation effective date (both under 42 CFR 418.24), via an
electronic 837I transaction using Type of Bill 81A / 81B (freestanding
hospice) or 82A / 82B (hospital-based) -- see
app.billing.services.noe_penalty_service / notr_penalty_service for the
late-filing penalty math this feeds.

This builder reuses the same segment-building primitives and validation
rules as the real claim 837I builder (edi_builder.py) so the two outputs
are structurally consistent; a NOE/NOTR carries no revenue/charge lines
(SV2/claim-line segments), only the header, patient, provider, and the
real occurrence-date value code for the election/discharge date.

Simplification (documented, not fabricated): the UB Type of Bill's second
digit (facility sub-type, freestanding vs. hospital-based) always uses
"1" (freestanding) since Tenant has no hospital-based/freestanding
distinction on file yet. Real hospital-based hospices would need "2".
"""

from datetime import date

from app.billing.services.edi_builder import (
    EDIBuilderError,
    _clean,
    _date_now,
    _hhmm_now,
    _segment,
    _validate_attending,
    _validate_claim_identity,
    _validate_provider_identity,
    _yyyymmdd,
)

# TOB (position 1 = facility type "8" hospice, position 2 = "1" freestanding
# (see simplification note above), position 3 = claim frequency code).
NOTICE_TOB_BY_TYPE = {
    "NOE": "81A",
    "NOTR": "81B",
}

# Real UB-04/837I occurrence codes: 27 = Hospice Election Date,
# 42 = Discharge Date.
NOTICE_OCCURRENCE_CODE_BY_TYPE = {
    "NOE": "27",
    "NOTR": "42",
}


def build_notice_837i_text(
    *,
    submission_type: str,
    control_number: str,
    effective_date: date,
    notice_export: dict,
) -> str:
    """
    Builds the raw 837I text for a NOE or NOTR notice.

    Args:
        submission_type: "NOE" or "NOTR".
        control_number: real claim control number for this notice
            (e.g. a fresh UUID).
        effective_date: the election effective date (NOE) or discharge/
            revocation effective date (NOTR).
        notice_export: the dict from
            notice_export_service.build_notice_export() (patient,
            provider, attending_provider, payer blocks).
    """
    if submission_type not in NOTICE_TOB_BY_TYPE:
        raise EDIBuilderError(f"Unsupported notice submission_type: {submission_type}")

    tob = NOTICE_TOB_BY_TYPE[submission_type]
    occurrence_code = NOTICE_OCCURRENCE_CODE_BY_TYPE[submission_type]

    patient = notice_export.get("patient", {})
    provider = notice_export.get("provider", {})
    attending = notice_export.get("attending_provider", {})
    payer = notice_export.get("payer", {})

    if not patient or not provider or not attending:
        raise EDIBuilderError("Missing required notice payload sections")

    patient_name = _clean(patient.get("patient_name"))
    patient_dob = _yyyymmdd(patient.get("date_of_birth"))
    subscriber_id = _clean(patient.get("subscriber_id"))
    subscriber_id_type = _clean(patient.get("subscriber_id_type")) or "MI"

    payer_obj = payer.get("primary_payer") or {}
    payer_name = _clean(payer_obj.get("payer_name"))
    payer_type = _clean(payer_obj.get("payer_type"))

    provider_name = _clean(provider.get("agency_name"))
    provider_npi = _clean(provider.get("npi"))
    provider_tax_id = _clean(provider.get("tax_id"))

    _validate_claim_identity(payer_type, subscriber_id, subscriber_id_type)
    _validate_provider_identity(provider_npi, provider_tax_id)
    _validate_attending(attending)

    segments: list[str] = []

    segments.append(_segment("ISA", "00", "", "00", "", "ZZ", "SNSHOSPICEEMR", "ZZ", "RECEIVER", _date_now(), _hhmm_now(), "^", "00501", "000000001", "0", "P", ":"))
    segments.append(_segment("GS", "HC", "SNSHOSPICEEMR", "RECEIVER", _date_now(), _hhmm_now(), "1", "X", "005010X223A2"))
    segments.append(_segment("ST", "837", "0001", "005010X223A2"))
    segments.append(_segment("BHT", "0019", "00", _clean(control_number), _date_now(), _hhmm_now(), "CH"))

    segments.append(_segment("NM1", "41", "2", provider_name, "", "", "", "", "46", "SUBMITTER"))
    segments.append(_segment("PER", "IC", "BILLING", "TE", "0000000000"))
    segments.append(_segment("NM1", "40", "2", payer_name, "", "", "", "", "46", "RECEIVER"))

    segments.append(_segment("HL", "1", "", "20", "1"))
    segments.append(_segment("PRV", "BI", "PXC", "251G00000X"))
    segments.append(_segment("NM1", "85", "2", provider_name, "", "", "", "", "XX", provider_npi))
    segments.append(_segment("REF", "EI", provider_tax_id))

    segments.append(_segment("HL", "2", "1", "22", "0"))
    segments.append(_segment("SBR", "P", "18"))
    segments.append(_segment("NM1", "IL", "1", patient_name, "", "", "", "", subscriber_id_type, subscriber_id))
    if patient_dob:
        segments.append(_segment("DMG", "D8", patient_dob))

    # CLM05 composite = Facility Type Code (TOB pos 1) : Facility Code
    # Qualifier (always "B") : Claim Frequency Type Code (TOB pos 3).
    # Built manually (not via _segment) because _segment's shared _clean()
    # helper strips ":" -- correct for a flat element, but this composite
    # sub-element separator must be preserved for a valid CLM05.
    clm05 = f"{tob[0]}:B:{tob[2]}"
    segments.append(
        "*".join(["CLM", _clean(control_number), "", "", "", clm05, "Y", "A", "Y", "I"]) + "~"
    )

    # Real occurrence-date value code carrying the election/discharge
    # effective date this notice is reporting. Built manually for the
    # same colon-preservation reason as CLM05 above.
    segments.append(f"HI*BH:{occurrence_code}:D8:{_yyyymmdd(str(effective_date))}~")

    segments.append(_segment("NM1", "71", "1", attending["last_name"], attending["first_name"], "", "", "", "XX", attending["npi"]))

    segments.append(_segment("SE", len(segments) + 1, "0001"))
    segments.append(_segment("GE", "1", "1"))
    segments.append(_segment("IEA", "1", "000000001"))

    return "\n".join(segments)
