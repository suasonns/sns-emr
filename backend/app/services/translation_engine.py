from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, List, Tuple

from app.schemas.translation import (
    BaselineChange,
    ClarificationItem,
    EligibilityDirection,
    InterpretationOutput,
    NormalizedObservations,
    OxygenDevice,
    OxygenMode,
    RiskLevel,
    TranslationMode,
    TranslationOutput,
    TranslationRealtimeResponse,
)


def _contains(text: str | None, needle: str) -> bool:
    return bool(text) and needle.lower() in text.lower()


def build_clarifications(observations: Dict[str, Any]) -> List[ClarificationItem]:
    items: List[ClarificationItem] = []

    oxygen_note = observations.get("oxygen_use_note")
    if oxygen_note:
        lower = oxygen_note.lower()
        has_lpm = "l" in lower or "liter" in lower
        has_mode = ("continuous" in lower) or ("prn" in lower)
        has_device = ("nc" in lower) or ("nasal cannula" in lower) or ("mask" in lower)

        if not has_lpm:
            items.append(
                ClarificationItem(
                    field="oxygen_use_note",
                    reason="insufficient specificity",
                    question="What is the current oxygen flow rate in L/min?",
                    required=True,
                )
            )
        if not has_mode:
            items.append(
                ClarificationItem(
                    field="oxygen_use_note",
                    reason="insufficient specificity",
                    question="Is the oxygen continuous or PRN?",
                    required=True,
                )
            )
        if not has_device:
            items.append(
                ClarificationItem(
                    field="oxygen_use_note",
                    reason="insufficient specificity",
                    question="What delivery device is being used (nasal cannula or mask)?",
                    required=True,
                )
            )

    if observations.get("transfer_change") and not observations.get("adl_notes"):
        items.append(
            ClarificationItem(
                field="transfer_change",
                reason="baseline comparison missing",
                question="Is increased transfer assistance compared with prior baseline?",
                required=True,
            )
        )

    if observations.get("current_orders_reported"):
        for order in observations["current_orders_reported"]:
            if "prn" not in order.lower() and "q" not in order.lower():
                items.append(
                    ClarificationItem(
                        field="current_orders_reported",
                        reason="dose/frequency incomplete",
                        question=f"Please confirm dose/frequency for order: {order}",
                        required=False,
                    )
                )

    return items


def normalize_observations(observations: Dict[str, Any]) -> NormalizedObservations:
    n = NormalizedObservations()

    # DME
    dme_items = observations.get("dme_items_reported") or []
    n.dme.items_in_use = [str(item).strip().upper().replace(" ", "_") for item in dme_items if str(item).strip()]

    # Orders
    orders = observations.get("current_orders_reported") or []
    n.orders.active_orders = [str(o).strip() for o in orders if str(o).strip()]

    # Intake
    intake = observations.get("intake_change")
    if intake:
        if _contains(intake, "less") or _contains(intake, "decrease"):
            n.intake.baseline_change = BaselineChange.DECREASED

    # Transfers / mobility
    transfer = observations.get("transfer_change")
    if transfer:
        if _contains(transfer, "more help") or _contains(transfer, "assist"):
            n.transfers.requires_assistance = True
            n.transfers.baseline_change = BaselineChange.WORSE

    mobility = observations.get("mobility_change")
    if mobility:
        if _contains(mobility, "worse") or _contains(mobility, "decline") or _contains(mobility, "weaker"):
            n.mobility_status.baseline_change = BaselineChange.WORSE

    # Sleep pattern
    sleep = observations.get("sleep_pattern_note")
    if sleep and (_contains(sleep, "sleeping more") or _contains(sleep, "more sleeping")):
        n.sleep_pattern.baseline_change = BaselineChange.INCREASED

    # Hospitalization
    hospitalization = observations.get("hospitalization_note")
    if hospitalization:
        n.hospitalization.report_present = True

    # Oxygen
    oxygen = observations.get("oxygen_use_note")
    if oxygen:
        lower = oxygen.lower()
        n.oxygen.in_use = True

        # Device
        if "nc" in lower or "nasal cannula" in lower:
            n.oxygen.device = OxygenDevice.NASAL_CANNULA
        elif "mask" in lower:
            n.oxygen.device = OxygenDevice.MASK

        # Mode
        if "continuous" in lower:
            n.oxygen.mode = OxygenMode.CONTINUOUS
        elif "prn" in lower:
            n.oxygen.mode = OxygenMode.PRN

        # Flow rate (simple parse)
        tokens = lower.replace("/", " ").split()
        for i, token in enumerate(tokens):
            if token.endswith("l") and token[:-1].replace(".", "", 1).isdigit():
                n.oxygen.flow_lpm = float(token[:-1])
                break
            if token.replace(".", "", 1).isdigit():
                if i + 1 < len(tokens) and tokens[i + 1].startswith("l"):
                    n.oxygen.flow_lpm = float(token)
                    break

    return n


def translate_observations(
    normalized: NormalizedObservations,
) -> Tuple[TranslationOutput, Dict[str, List[str]]]:
    lines: List[str] = []
    source_map: Dict[str, List[str]] = {}

    if normalized.oxygen.in_use:
        device = normalized.oxygen.device.value.replace("_", " ").lower()
        mode = normalized.oxygen.mode.value.lower()
        flow = normalized.oxygen.flow_lpm
        if flow is not None and normalized.oxygen.device != OxygenDevice.UNKNOWN and normalized.oxygen.mode != OxygenMode.UNKNOWN:
            line = f"Patient currently uses oxygen at {flow:g} L/min {mode} via {device}."
        elif flow is not None:
            line = f"Patient currently uses oxygen at {flow:g} L/min."
        else:
            line = "Patient currently uses oxygen."
        lines.append(line)
        source_map[f"translated_narrative[{len(lines)-1}]"] = ["observations.oxygen_use_note"]

    if normalized.dme.items_in_use:
        pretty = ", ".join(item.replace("_", " ").lower() for item in normalized.dme.items_in_use)
        lines.append(f"DME in use includes {pretty}.")
        source_map[f"translated_narrative[{len(lines)-1}]"] = ["observations.dme_items_reported"]

    if normalized.transfers.requires_assistance and normalized.transfers.baseline_change == BaselineChange.WORSE:
        lines.append("Patient requires increased assistance with transfers compared with prior baseline.")
        source_map[f"translated_narrative[{len(lines)-1}]"] = ["observations.transfer_change", "observations.adl_notes"]

    if normalized.intake.baseline_change == BaselineChange.DECREASED:
        lines.append("Oral intake is decreased.")
        source_map[f"translated_narrative[{len(lines)-1}]"] = ["observations.intake_change"]

    if normalized.orders.active_orders:
        pretty_orders = "; ".join(normalized.orders.active_orders)
        lines.append(f"Current orders reported include {pretty_orders}.")
        source_map[f"translated_narrative[{len(lines)-1}]"] = ["observations.current_orders_reported"]

    output = TranslationOutput(
        translated_narrative=lines,
        translation_mode_used=TranslationMode.DETERMINISTIC,
        generated_at=datetime.utcnow(),
        review_required=True,
    )
    return output, source_map


def interpret_observations(normalized: NormalizedObservations) -> InterpretationOutput:
    functional_decline = (
        normalized.transfers.requires_assistance
        or normalized.mobility_status.baseline_change == BaselineChange.WORSE
    )
    nutritional_decline = normalized.intake.baseline_change == BaselineChange.DECREASED
    clinical_decline = normalized.oxygen.in_use or normalized.hospitalization.report_present

    risk_score = sum([functional_decline, nutritional_decline, clinical_decline])

    if risk_score >= 3:
        risk_level = RiskLevel.HIGH
        eligibility = EligibilityDirection.RECERTIFY
    elif risk_score == 2:
        risk_level = RiskLevel.MEDIUM
        eligibility = EligibilityDirection.UNDECIDED
    else:
        risk_level = RiskLevel.LOW
        eligibility = EligibilityDirection.UNDECIDED

    missing = []

    return InterpretationOutput(
        functional_decline=functional_decline,
        nutritional_decline=nutritional_decline,
        clinical_decline=clinical_decline,
        risk_level=risk_level,
        eligibility_direction=eligibility,
        missing_required_elements=missing,
    )


def run_realtime_translation(observations: Dict[str, Any]) -> TranslationRealtimeResponse:
    clarifications = build_clarifications(observations)
    normalized = normalize_observations(observations)
    translation_output, source_map = translate_observations(normalized)
    interpretation_output = interpret_observations(normalized)

    return TranslationRealtimeResponse(
        clarification_items=clarifications,
        normalized_observations_json=normalized,
        translation_output_json=translation_output,
        interpretation_output_json=interpretation_output,
        translation_source_map_json=source_map,
    )
