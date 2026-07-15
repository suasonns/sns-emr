from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


# =========================================================
# ENUMS
# =========================================================

class AcuityState(str, Enum):
    ROUTINE = "ROUTINE"
    CRISIS = "CRISIS"


class CareModel(str, Enum):
    RN_ONLY = "RN_ONLY"
    RN_PLUS_LVN = "RN_PLUS_LVN"
    RN_PLUS_CHHA = "RN_PLUS_CHHA"
    RN_PLUS_LVN_CHHA = "RN_PLUS_LVN_CHHA"


class PocTriggerPolicy(str, Enum):
    """
    Canonical POC trigger policies.

    Locked Phase 1 rule:
    - Routine PERIODIC POC_UPDATE anchoring requires a supervisory RN visit.
    - Crisis same-day behavior is separate and uses same-day RN clinical review behavior.
    - Wounds may influence condition-specific reassessment cadence, but they do not
      override the supervisory RN requirement for routine PERIODIC POC_UPDATE anchoring.

    Legacy drift policies are intentionally retained for defensive compatibility only.
    They must not be emitted by determine_care_model().
    """

    SUPERVISORY_RN_ONLY = "SUPERVISORY_RN_ONLY"
    SAME_DAY_ANY_RN_CRISIS = "SAME_DAY_ANY_RN_CRISIS"

    # Legacy compatibility values.
    # These must not be returned by determine_care_model().
    ANY_RN = "ANY_RN"
    ANY_RN_WOUND_OVERRIDE = "ANY_RN_WOUND_OVERRIDE"


# =========================================================
# CONSTANTS
# =========================================================

DEFAULT_POC_CYCLE_DAYS = 14


# =========================================================
# DECISION MODEL
# =========================================================

@dataclass(frozen=True)
class CareModelDecision:
    """
    Immutable care model decision.

    Important semantic boundaries:
    - supervisory_required describes whether a supervisory RN visit is required
      to anchor routine PERIODIC POC_UPDATE behavior.
    - poc_trigger_policy describes how POC_UPDATE automation should interpret
      finalized RN visits.
    - has_wounds is a clinical condition flag and does not automatically mean
      any RN visit can anchor periodic POC behavior.
    """

    care_model: CareModel
    supervisory_required: bool
    poc_trigger_policy: PocTriggerPolicy
    poc_due_days: int
    has_support_staff: bool
    has_wounds: bool
    acuity_state: AcuityState
    reason: str


# =========================================================
# NORMALIZATION HELPERS
# =========================================================

def normalize_acuity_state(value: Optional[str]) -> AcuityState:
    """
    Normalize acuity state into a safe canonical enum.

    Default:
    - ROUTINE

    Accepted:
    - CRISIS
    - ROUTINE

    Unknown values safely resolve to ROUTINE.
    """

    if not value:
        return AcuityState.ROUTINE

    normalized = str(value).strip().upper()

    if normalized == AcuityState.CRISIS.value:
        return AcuityState.CRISIS

    return AcuityState.ROUTINE


def _determine_care_model(
    *,
    has_chha: bool,
    has_lvn: bool,
) -> CareModel:
    """
    Determine the staffing care model from patient support flags.
    """

    chha = bool(has_chha)
    lvn = bool(has_lvn)

    if lvn and chha:
        return CareModel.RN_PLUS_LVN_CHHA

    if lvn:
        return CareModel.RN_PLUS_LVN

    if chha:
        return CareModel.RN_PLUS_CHHA

    return CareModel.RN_ONLY


def _has_support_staff(
    *,
    has_chha: bool,
    has_lvn: bool,
) -> bool:
    """
    Return whether the patient has delegated support staff.

    Support staff currently means:
    - CHHA
    - LVN
    """

    return bool(has_chha or has_lvn)


def _is_visit_marked_supervisory(visit) -> bool:
    """
    Determine whether a visit is explicitly marked as supervisory.

    Important:
    - INITIAL_RN_ICA is NOT supervisory.
    - Routine RN visit is NOT automatically supervisory.
    - Supervisory status must come from:
        1. visit.is_supervisory = True
        2. form_type == SUPV_VISIT_ONLY
        3. visit.details["is_supervisory"] = True

    This function is defensive because Visit rows may not all have
    the same attributes during development/migration.
    """

    if visit is None:
        return False

    form_type = str(getattr(visit, "form_type", "") or "").strip().upper()

    if form_type == "SUPV_VISIT_ONLY":
        return True

    if bool(getattr(visit, "is_supervisory", False)):
        return True

    details = getattr(visit, "details", None)

    if isinstance(details, dict):
        if bool(details.get("is_supervisory", False)):
            return True

    return False


# =========================================================
# PUBLIC DOMAIN API
# =========================================================

def determine_care_model(
    *,
    has_chha: bool,
    has_lvn: bool,
    has_wounds: bool,
    acuity_state: Optional[str],
) -> CareModelDecision:
    """
    Determine the patient's care model and POC trigger policy.

    Locked Phase 1 policy:

    CRISIS:
      - Same-day RN POC review behavior may be triggered by any finalized RN visit.
      - This is not the routine PERIODIC cycle anchor.
      - Output policy: SAME_DAY_ANY_RN_CRISIS
      - Due days: 0

    ROUTINE:
      - Routine PERIODIC POC_UPDATE anchoring requires supervisory RN visit.
      - This applies to:
          1. RN-only patients
          2. RN + LVN patients
          3. RN + CHHA patients
          4. RN + LVN + CHHA patients
          5. patients with wounds
      - Output policy: SUPERVISORY_RN_ONLY
      - Due days: 14

    Wounds:
      - Wounds may create condition-specific reassessment needs.
      - Wounds do not allow a non-supervisory RN visit to anchor routine PERIODIC
        POC_UPDATE behavior.
      - Wound cadence belongs to condition-specific reassessment logic, not to the
        routine POC_UPDATE anchor rule.

    This function must never emit:
    - ANY_RN
    - ANY_RN_WOUND_OVERRIDE
    """

    normalized_has_chha = bool(has_chha)
    normalized_has_lvn = bool(has_lvn)
    normalized_has_wounds = bool(has_wounds)

    acuity = normalize_acuity_state(acuity_state)

    support_present = _has_support_staff(
        has_chha=normalized_has_chha,
        has_lvn=normalized_has_lvn,
    )

    care_model = _determine_care_model(
        has_chha=normalized_has_chha,
        has_lvn=normalized_has_lvn,
    )

    # ---------------------------------------------------------
    # CRISIS:
    # Same-day RN review behavior, not routine periodic anchoring.
    # ---------------------------------------------------------
    if acuity == AcuityState.CRISIS:
        return CareModelDecision(
            care_model=care_model,
            supervisory_required=False,
            poc_trigger_policy=PocTriggerPolicy.SAME_DAY_ANY_RN_CRISIS,
            poc_due_days=0,
            has_support_staff=support_present,
            has_wounds=normalized_has_wounds,
            acuity_state=acuity,
            reason=(
                "CRISIS: any finalized RN visit may trigger same-day POC_UPDATE review. "
                "This is same-day crisis behavior and does not establish routine PERIODIC anchoring."
            ),
        )

    # ---------------------------------------------------------
    # ROUTINE WITH WOUNDS:
    # Supervisory RN still required for routine periodic POC anchoring.
    # ---------------------------------------------------------
    if normalized_has_wounds:
        return CareModelDecision(
            care_model=care_model,
            supervisory_required=True,
            poc_trigger_policy=PocTriggerPolicy.SUPERVISORY_RN_ONLY,
            poc_due_days=DEFAULT_POC_CYCLE_DAYS,
            has_support_staff=support_present,
            has_wounds=True,
            acuity_state=acuity,
            reason=(
                "ROUTINE with wounds: wounds may require condition-specific reassessment cadence, "
                "but routine PERIODIC POC_UPDATE anchoring still requires a supervisory RN visit."
            ),
        )

    # ---------------------------------------------------------
    # ROUTINE WITH SUPPORT STAFF:
    # LVN/CHHA support requires supervisory RN anchor.
    # ---------------------------------------------------------
    if support_present:
        return CareModelDecision(
            care_model=care_model,
            supervisory_required=True,
            poc_trigger_policy=PocTriggerPolicy.SUPERVISORY_RN_ONLY,
            poc_due_days=DEFAULT_POC_CYCLE_DAYS,
            has_support_staff=True,
            has_wounds=False,
            acuity_state=acuity,
            reason=(
                "ROUTINE with LVN/CHHA support: supervisory RN visit is required to anchor "
                "routine PERIODIC POC_UPDATE behavior."
            ),
        )

    # ---------------------------------------------------------
    # ROUTINE RN-ONLY:
    # Locked Phase 1 rule still requires supervisory RN anchor.
    # ---------------------------------------------------------
    return CareModelDecision(
        care_model=CareModel.RN_ONLY,
        supervisory_required=True,
        poc_trigger_policy=PocTriggerPolicy.SUPERVISORY_RN_ONLY,
        poc_due_days=DEFAULT_POC_CYCLE_DAYS,
        has_support_staff=False,
        has_wounds=False,
        acuity_state=acuity,
        reason=(
            "ROUTINE RN-only: routine PERIODIC POC_UPDATE anchoring requires a supervisory RN visit. "
            "Non-supervisory RN visits do not anchor the next 14-day periodic POC cycle."
        ),
    )


def should_anchor_poc_from_rn_visit(
    *,
    visit,
    decision: CareModelDecision,
) -> bool:
    """
    Determine whether a finalized RN visit may anchor POC_UPDATE behavior.

    Locked Phase 1 behavior:

    CRISIS:
      - SAME_DAY_ANY_RN_CRISIS returns True because crisis behavior is same-day
        operational review behavior.

    ROUTINE:
      - SUPERVISORY_RN_ONLY returns True only when the visit is explicitly marked supervisory.
      - Non-supervisory RN visits must not anchor routine PERIODIC POC_UPDATE behavior.

    Legacy defensive behavior:
      - If a legacy decision object with ANY_RN or ANY_RN_WOUND_OVERRIDE reaches this
        function, the function still requires supervisory RN anchoring unless the policy
        is explicitly SAME_DAY_ANY_RN_CRISIS.
      - This prevents old policy values from reintroducing drift.
    """

    if decision is None:
        return False

    is_supervisory = _is_visit_marked_supervisory(visit)

    # ---------------------------------------------------------
    # CRISIS:
    # Any finalized RN visit may trigger same-day POC review.
    # This is not routine periodic anchoring.
    # ---------------------------------------------------------
    if decision.poc_trigger_policy == PocTriggerPolicy.SAME_DAY_ANY_RN_CRISIS:
        return True

    # ---------------------------------------------------------
    # ROUTINE:
    # Supervisory RN only.
    # ---------------------------------------------------------
    if decision.poc_trigger_policy == PocTriggerPolicy.SUPERVISORY_RN_ONLY:
        return bool(is_supervisory)

    # ---------------------------------------------------------
    # LEGACY / DEFENSIVE:
    # Do not allow ANY_RN or ANY_RN_WOUND_OVERRIDE to bypass the
    # supervisory requirement for routine periodic POC updates.
    # ---------------------------------------------------------
    return bool(is_supervisory)