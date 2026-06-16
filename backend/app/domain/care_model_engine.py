from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AcuityState(str, Enum):
    ROUTINE = "ROUTINE"
    CRISIS = "CRISIS"


class CareModel(str, Enum):
    RN_ONLY = "RN_ONLY"
    RN_PLUS_LVN = "RN_PLUS_LVN"
    RN_PLUS_CHHA = "RN_PLUS_CHHA"
    RN_PLUS_LVN_CHHA = "RN_PLUS_LVN_CHHA"


class PocTriggerPolicy(str, Enum):
    ANY_RN = "ANY_RN"
    SUPERVISORY_RN_ONLY = "SUPERVISORY_RN_ONLY"
    ANY_RN_WOUND_OVERRIDE = "ANY_RN_WOUND_OVERRIDE"
    SAME_DAY_ANY_RN_CRISIS = "SAME_DAY_ANY_RN_CRISIS"


@dataclass(frozen=True)
class CareModelDecision:
    care_model: CareModel
    supervisory_required: bool
    poc_trigger_policy: PocTriggerPolicy
    poc_due_days: int
    has_support_staff: bool
    has_wounds: bool
    acuity_state: AcuityState
    reason: str


def normalize_acuity_state(value: Optional[str]) -> AcuityState:
    if not value:
        return AcuityState.ROUTINE
    normalized = str(value).strip().upper()
    if normalized == AcuityState.CRISIS.value:
        return AcuityState.CRISIS
    return AcuityState.ROUTINE


def determine_care_model(
    *,
    has_chha: bool,
    has_lvn: bool,
    has_wounds: bool,
    acuity_state: Optional[str],
) -> CareModelDecision:
    acuity = normalize_acuity_state(acuity_state)
    support_present = bool(has_chha or has_lvn)

    if has_lvn and has_chha:
        care_model = CareModel.RN_PLUS_LVN_CHHA
    elif has_lvn:
        care_model = CareModel.RN_PLUS_LVN
    elif has_chha:
        care_model = CareModel.RN_PLUS_CHHA
    else:
        care_model = CareModel.RN_ONLY

    # Highest-priority override: CRISIS
    # Rule: every RN visit triggers same-day POC
    if acuity == AcuityState.CRISIS:
        return CareModelDecision(
            care_model=care_model,
            supervisory_required=False,
            poc_trigger_policy=PocTriggerPolicy.SAME_DAY_ANY_RN_CRISIS,
            poc_due_days=0,
            has_support_staff=support_present,
            has_wounds=bool(has_wounds),
            acuity_state=acuity,
            reason="CRISIS override: every finalized RN visit triggers same-day POC.",
        )

    # Routine + wounds override
    # Rule: POC updated every 14 days regardless of supervisory visits
    if has_wounds:
        return CareModelDecision(
            care_model=care_model,
            supervisory_required=support_present,
            poc_trigger_policy=PocTriggerPolicy.ANY_RN_WOUND_OVERRIDE,
            poc_due_days=14,
            has_support_staff=support_present,
            has_wounds=True,
            acuity_state=acuity,
            reason="Wound override: any finalized RN visit may anchor the next 14-day POC cycle.",
        )

    # Routine RN-only
    # Rule: no supervisory requirement, any RN visit anchors POC
    if not support_present:
        return CareModelDecision(
            care_model=CareModel.RN_ONLY,
            supervisory_required=False,
            poc_trigger_policy=PocTriggerPolicy.ANY_RN,
            poc_due_days=14,
            has_support_staff=False,
            has_wounds=False,
            acuity_state=acuity,
            reason="Routine RN-only: supervisory visit not required; any finalized RN visit anchors POC.",
        )

    # Routine with support staff
    # Rule: supervisory RN visits required; only supervisory RN visit anchors POC
    return CareModelDecision(
        care_model=care_model,
        supervisory_required=True,
        poc_trigger_policy=PocTriggerPolicy.SUPERVISORY_RN_ONLY,
        poc_due_days=14,
        has_support_staff=True,
        has_wounds=False,
        acuity_state=acuity,
        reason="Routine with LVN/CHHA support: supervisory RN visit required and anchors POC.",
    )


def should_anchor_poc_from_rn_visit(
    *,
    is_supervisory_visit: bool,
    decision: CareModelDecision,
) -> bool:
    if decision.poc_trigger_policy == PocTriggerPolicy.SAME_DAY_ANY_RN_CRISIS:
        return True

    if decision.poc_trigger_policy == PocTriggerPolicy.ANY_RN:
        return True

    if decision.poc_trigger_policy == PocTriggerPolicy.ANY_RN_WOUND_OVERRIDE:
        return True

    if decision.poc_trigger_policy == PocTriggerPolicy.SUPERVISORY_RN_ONLY:
        return bool(is_supervisory_visit)

    return False