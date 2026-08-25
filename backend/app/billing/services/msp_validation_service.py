from __future__ import annotations

"""
Medicare Secondary Payer (MSP) claim-sequencing engine.

Real CMS rule set this module implements:

1. Every institutional claim (837I) must carry an unambiguous payer
   sequence (SBR01: "P" primary, "S" secondary, "T" tertiary...). When a
   patient has an MSP-type payer on file (a payer that is, by CMS
   definition, primary to Medicare for the service period in question),
   Medicare CANNOT be billed as primary -- doing so results in the claim
   being returned/denied (RTP) or, if it slips through, a real MSP
   recoupment demand later. This has real financial and compliance
   consequences, not just a data-quality nuisance.

2. CMS MSP Type/Value codes (42 CFR 411 subpart B; CMS IOM Pub 100-05).
   Each MSP type code identifies the situation making a non-Medicare payer
   primary to Medicare for the relevant condition/period:
     12 = Working Aged (employer Group Health Plan, employee/spouse 65+)
     13 = ESRD (12-month coordination period)
     14 = No-Fault / Auto insurance (up to policy limits)
     15 = Workers' Compensation
     16 = Public Health Service / other federal agency
     41 = Black Lung
     42 = Veterans Affairs
     43 = Disability (Large Group Health Plan, employee/family <65,
          disabled)
     47 = Liability insurance (including self-insurance)
   These map to real UB-04/837I value codes (12-16, 41-43, 47) carried on
   the claim so the payer/MAC knows which coordination rule applied.

3. Sequencing logic, in priority order:
   a. An explicit `priority_order` on file is authoritative when present
      and internally consistent (no two payers share the same order, and
      order 1 is not assigned to a payer with an active msp_type_code
      unless there truly is no Medicare payer on file at all -- Medicare
      itself is never assigned an msp_type_code, since msp_type_code
      describes the *other* payer's relationship to Medicare).
   b. If no explicit ordering exists, any active (date-overlapping)
      msp_type_code payer is placed ahead of Medicare automatically --
      Medicare is inferred secondary.
   c. Multiple active MSP-type payers with no explicit priority_order
      between them, or a priority_order that conflicts with an active MSP
      relationship (e.g. Medicare marked priority_order=1 while a Workers'
      Comp payer with an overlapping msp_type_code has no order at all),
      is a genuine ambiguity -- this module NEVER guesses; it returns a
      conflict reason so the caller can block claim generation instead of
      silently billing Medicare as primary.

This module is pure (no DB access) so it can be unit tested directly and
reused by both claim_export_service.py (build the payer block) and
edi_builder.py (gate + build the SBR segment).
"""

from dataclasses import dataclass, field
from datetime import date

# Real CMS MSP value codes -> UB-04 value code + short description.
MSP_VALUE_CODES: dict[str, str] = {
    "12": "Working Aged (Employer Group Health Plan)",
    "13": "End-Stage Renal Disease (ESRD) coordination period",
    "14": "No-Fault / Automobile Insurance",
    "15": "Workers' Compensation",
    "16": "Public Health Service (PHS) or Other Federal Agency",
    "41": "Black Lung",
    "42": "Veterans Affairs (VA)",
    "43": "Disability (Large Group Health Plan)",
    "47": "Liability Insurance (including self-insured)",
}

MEDICARE_PAYER_TYPES = {"MEDICARE", "MEDICARE_HOSPICE"}

SBR_SEQUENCE_CODES = ["P", "S", "T", "A", "B", "C", "D", "E", "F", "G"]


class MspValidationError(RuntimeError):
    pass


@dataclass(frozen=True)
class ResolvedPayer:
    payer_id: str | None
    payer_name: str | None
    payer_type: str | None
    subscriber_id: str | None
    subscriber_id_type: str | None
    msp_type_code: str | None
    sequence_code: str  # "P" / "S" / "T" / ...
    priority_order: int


@dataclass(frozen=True)
class MspSequenceResult:
    payers: list[ResolvedPayer] = field(default_factory=list)
    has_conflict: bool = False
    conflict_reason: str | None = None

    @property
    def primary(self) -> ResolvedPayer | None:
        return self.payers[0] if self.payers else None


def _is_active(payer: dict, as_of_date: date) -> bool:
    start = payer.get("effective_start_date")
    end = payer.get("end_date")
    if start and as_of_date < start:
        return False
    if end and as_of_date > end:
        return False
    return True


def _is_medicare(payer: dict) -> bool:
    return (payer.get("payer_type") or "").upper() in MEDICARE_PAYER_TYPES


def validate_msp_type_code(msp_type_code: str | None) -> None:
    if msp_type_code is None:
        return
    if msp_type_code not in MSP_VALUE_CODES:
        raise MspValidationError(
            f"Unknown MSP type code '{msp_type_code}'. Recognized CMS "
            f"value codes: {sorted(MSP_VALUE_CODES)}"
        )


def resolve_payer_sequence(
    payers: list[dict],
    *,
    service_date: date,
) -> MspSequenceResult:
    """
    Resolves the real, claim-ready payer sequence for a service date.

    Args:
        payers: raw patient_payers rows (dicts) with at least
            payer_name, payer_type, subscriber_id, subscriber_id_type,
            effective_start_date, end_date, is_primary, msp_type_code,
            priority_order.
        service_date: the date of service being billed (typically the
            claim's statement_from_date) -- only payers whose coverage
            window is active on this date are considered.

    Returns:
        MspSequenceResult. When has_conflict is True, `payers` is empty
        and callers MUST refuse to generate/submit the claim until the
        conflict is resolved (do not default to "Medicare primary").
    """
    if not payers:
        return MspSequenceResult(
            payers=[], has_conflict=True,
            conflict_reason="No payers on file for this patient at all.",
        )

    active = [p for p in payers if _is_active(p, service_date)]
    if not active:
        return MspSequenceResult(
            payers=[], has_conflict=True,
            conflict_reason=(
                f"No payer has an active coverage window on {service_date.isoformat()}."
            ),
        )

    for p in active:
        try:
            validate_msp_type_code(p.get("msp_type_code"))
        except MspValidationError as exc:
            return MspSequenceResult(payers=[], has_conflict=True, conflict_reason=str(exc))

    medicare_payers = [p for p in active if _is_medicare(p)]
    if len(medicare_payers) > 1:
        return MspSequenceResult(
            payers=[], has_conflict=True,
            conflict_reason="More than one active Medicare payer on file -- cannot resolve sequence.",
        )

    # A payer of type MEDICARE should never itself carry an msp_type_code
    # (that field describes another payer's relationship TO Medicare).
    for p in medicare_payers:
        if p.get("msp_type_code"):
            return MspSequenceResult(
                payers=[], has_conflict=True,
                conflict_reason=(
                    "Medicare payer record has an msp_type_code set -- "
                    "msp_type_code belongs on the OTHER payer that is "
                    "primary to Medicare, not on the Medicare record itself."
                ),
            )

    explicit_orders = [p.get("priority_order") for p in active if p.get("priority_order") is not None]
    if len(explicit_orders) != len(set(explicit_orders)):
        return MspSequenceResult(
            payers=[], has_conflict=True,
            conflict_reason="Two or more active payers share the same priority_order.",
        )

    msp_payers = [p for p in active if p.get("msp_type_code")]

    if explicit_orders:
        # Explicit ordering present -- it must be complete (every active
        # payer has one), gapless (1..N, no skipped/duplicate ranks), and
        # internally consistent with any MSP data.
        missing_order = [p for p in active if p.get("priority_order") is None]
        if missing_order:
            names = ", ".join(p.get("payer_name") or "unknown" for p in missing_order)
            return MspSequenceResult(
                payers=[], has_conflict=True,
                conflict_reason=(
                    "Some active payers have an explicit priority_order and "
                    f"others don't ({names}) -- ordering must be all-or-nothing."
                ),
            )

        sorted_orders = sorted(explicit_orders)
        if sorted_orders != list(range(1, len(active) + 1)):
            return MspSequenceResult(
                payers=[], has_conflict=True,
                conflict_reason=(
                    f"priority_order values {sorted_orders} are not a clean "
                    f"1..{len(active)} sequence -- fix gaps/duplicates before billing."
                ),
            )

        ordered = sorted(active, key=lambda p: p["priority_order"])

        medicare_order = next((m["priority_order"] for m in medicare_payers), None)
        if medicare_order is not None:
            for p in msp_payers:
                if p["priority_order"] > medicare_order:
                    return MspSequenceResult(
                        payers=[], has_conflict=True,
                        conflict_reason=(
                            f"{p.get('payer_name')} carries MSP type code "
                            f"{p.get('msp_type_code')} "
                            f"({MSP_VALUE_CODES.get(p.get('msp_type_code'))}) but is "
                            "sequenced AFTER Medicare -- an MSP payer must always be "
                            "primary to Medicare for the covered condition."
                        ),
                    )
    else:
        # No explicit ordering on file. Resolve deterministically instead
        # of guessing:
        #   1. An active MSP-type payer is always primary to Medicare --
        #      that is the real CMS rule, independent of any is_primary
        #      flag. Two or more active MSP payers with no explicit order
        #      between them is a genuine ambiguity (which condition/payer
        #      governs first cannot be inferred) -- conflict.
        #   2. With zero or one MSP payer resolved, any remaining
        #      non-Medicare, non-MSP payers are ordered by is_primary,
        #      then by effective_start_date (earliest coverage first) as
        #      a deterministic, documented tiebreak -- never a coin flip.
        if len(msp_payers) > 1:
            names = ", ".join(p.get("payer_name") or "unknown" for p in msp_payers)
            return MspSequenceResult(
                payers=[], has_conflict=True,
                conflict_reason=(
                    f"Multiple active MSP-type payers ({names}) with no "
                    "explicit priority_order to sequence them relative to "
                    "each other and to Medicare."
                ),
            )

        msp_ids = {id(p) for p in msp_payers}
        medicare_ids = {id(p) for p in medicare_payers}
        remaining = [p for p in active if id(p) not in msp_ids and id(p) not in medicare_ids]

        if msp_payers:
            # An MSP payer already resolves who's primary -- any other
            # payer independently flagged is_primary=True contradicts it.
            conflicting_primary = [p for p in remaining if p.get("is_primary")]
            if conflicting_primary:
                names = ", ".join(p.get("payer_name") or "unknown" for p in conflicting_primary)
                return MspSequenceResult(
                    payers=[], has_conflict=True,
                    conflict_reason=(
                        f"{msp_payers[0].get('payer_name')} is an active MSP payer "
                        f"(must be primary), but {names} is also flagged "
                        "is_primary=True -- contradictory payer data."
                    ),
                )
            remaining_sorted = sorted(
                remaining, key=lambda p: p.get("effective_start_date") or date.min
            )
            ordered = msp_payers + medicare_payers + remaining_sorted
        else:
            primary_flagged = [p for p in remaining if p.get("is_primary")]
            if len(primary_flagged) > 1:
                names = ", ".join(p.get("payer_name") or "unknown" for p in primary_flagged)
                return MspSequenceResult(
                    payers=[], has_conflict=True,
                    conflict_reason=(
                        "Multiple payers flagged is_primary=True with no "
                        f"explicit priority_order to break the tie: {names}"
                    ),
                )
            if not primary_flagged and not medicare_payers and len(remaining) > 1:
                return MspSequenceResult(
                    payers=[], has_conflict=True,
                    conflict_reason=(
                        "Multiple active non-Medicare payers with no "
                        "is_primary flag or priority_order set -- cannot "
                        "determine claim sequence."
                    ),
                )

            flagged_ids = {id(p) for p in primary_flagged}
            unflagged_remaining = sorted(
                [p for p in remaining if id(p) not in flagged_ids],
                key=lambda p: p.get("effective_start_date") or date.min,
            )
            ordered = primary_flagged + medicare_payers + unflagged_remaining

    resolved: list[ResolvedPayer] = []
    for idx, p in enumerate(ordered):
        if idx >= len(SBR_SEQUENCE_CODES):
            return MspSequenceResult(
                payers=[], has_conflict=True,
                conflict_reason="More active payers than supported SBR sequence codes.",
            )
        resolved.append(
            ResolvedPayer(
                payer_id=str(p.get("id")) if p.get("id") is not None else None,
                payer_name=p.get("payer_name"),
                payer_type=p.get("payer_type"),
                subscriber_id=p.get("subscriber_id"),
                subscriber_id_type=p.get("subscriber_id_type"),
                msp_type_code=p.get("msp_type_code"),
                sequence_code=SBR_SEQUENCE_CODES[idx],
                priority_order=idx + 1,
            )
        )

    return MspSequenceResult(payers=resolved, has_conflict=False, conflict_reason=None)


def build_msp_value_codes_for_claim(sequence: MspSequenceResult) -> list[dict]:
    """
    Builds the UB-04/837I value-code entries (HI segment, qualifier "BE")
    required whenever an MSP-type payer is on the claim -- these tell the
    MAC which coordination rule was applied so it doesn't independently
    flag the claim for MSP development.
    """
    value_codes: list[dict] = []
    for p in sequence.payers:
        if p.msp_type_code:
            value_codes.append(
                {
                    "value_code": p.msp_type_code,
                    "description": MSP_VALUE_CODES.get(p.msp_type_code, "Unknown"),
                    "payer_name": p.payer_name,
                }
            )
    return value_codes
