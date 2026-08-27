# app/services/rnica_finalization_service.py
"""RN ICA SECTION 12 — Final Review, Signature & Finalization.

Single source of truth for "is this RN ICA assessment ready to lock?" so
the frontend Final Review Dashboard and the backend lock endpoint can
never disagree (the backend re-checks everything here before locking —
a disabled Lock button in the UI is a courtesy, not the enforcement
boundary).

Layer 1 (attestation / signature) and Layer 2 (POC completeness,
narrative review, LCD baseline, referrals reviewed) checks are
intentionally kept in one place, expressed as pure functions over
already-loaded data, so they are independently testable without a
live HTTP request.
"""

from __future__ import annotations

from typing import Any, Optional


def _get(form_data: dict, *path: str) -> Any:
    node: Any = form_data or {}
    for key in path:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


def _has_text(value: Optional[str]) -> bool:
    return isinstance(value, str) and value.strip() != ""


def evaluate_poc_completeness(problems: list[dict[str, Any]]) -> dict[str, Any]:
    """SECTION 11/12 — "Required POCs reviewed / Goals present /
    Interventions present / Disciplines assigned / Frequencies assigned."

    A patient with no active Plan of Care problems has nothing to validate
    (RN ICA locking must never *require* a problem to exist — see
    `test_lock_rnica_assessment_creates_no_poc_version_or_problem`). But any
    active problem that *does* exist must have >=1 goal, each goal must have
    >=1 intervention, and each intervention must carry an assigned
    discipline. (Frequency is not yet a capturable field on a POC
    intervention anywhere in the write path — see rnica_poc_adapter.py — so
    it is intentionally not enforced here until that data model exists.)
    """
    active_problems = [
        p for p in (problems or [])
        if p.get("status") not in ("RESOLVED", "HISTORICAL", "SUPERSEDED")
    ]

    if not active_problems:
        return {
            "ready": True,
            "message": "No active Plan of Care problems recorded; nothing to validate.",
            "incomplete_labels": [],
        }

    incomplete_labels: list[str] = []
    for problem in active_problems:
        goals = problem.get("goals") or []
        if not goals:
            incomplete_labels.append(problem.get("label") or problem.get("rule_key") or "Unlabeled problem")
            continue
        problem_incomplete = False
        for goal in goals:
            interventions = goal.get("interventions") or []
            if not interventions:
                problem_incomplete = True
                break
            for intervention in interventions:
                if not intervention.get("discipline"):
                    problem_incomplete = True
                    break
            if problem_incomplete:
                break
        if problem_incomplete:
            incomplete_labels.append(problem.get("label") or problem.get("rule_key") or "Unlabeled problem")

    if incomplete_labels:
        return {
            "ready": False,
            "message": (
                "Every active Plan of Care problem needs at least one goal, each goal needs at least one "
                "intervention, and each intervention needs an assigned discipline."
            ),
            "incomplete_labels": incomplete_labels,
        }

    return {"ready": True, "message": "All active Plan of Care problems have goals, interventions, and disciplines.", "incomplete_labels": []}


def evaluate_finalization_readiness(form_data: dict[str, Any], poc_problems: list[dict[str, Any]]) -> dict[str, Any]:
    """Returns the full SECTION 12 readiness breakdown. `checks` keys are
    stable identifiers the frontend renders as a checklist; `ready` is the
    single aggregate gate for the Lock action.
    """
    form_data = form_data or {}
    checks: dict[str, dict[str, Any]] = {}

    # --- Layer 1: attestation, signature ------------------------------
    signature_certification = _get(form_data, "finalization", "signatureCertification") is True
    checks["attestation"] = {
        "label": "Attestation",
        "ready": signature_certification,
        "message": "Clinician must certify this assessment is complete and accurate."
        if not signature_certification else "Attestation certified.",
    }

    clinician_signature = _get(form_data, "finalization", "clinicianSignature")
    checks["signature"] = {
        "label": "Required signatures present",
        "ready": _has_text(clinician_signature),
        "message": "Clinician signature is required." if not _has_text(clinician_signature) else "Signature present.",
    }

    # --- Layer 2: narrative, LCD baseline, decline baseline, referrals,
    # POC completeness --------------------------------------------------
    narrative = _get(form_data, "diagnoses", "clinicalNarrative")
    narrative_reviewed = _get(form_data, "diagnoses", "clinicalNarrativeReviewed") is True
    narrative_ready = (not _has_text(narrative)) or narrative_reviewed
    checks["narrativeReviewed"] = {
        "label": "Narrative reviewed",
        "ready": narrative_ready,
        "message": "Clinical narrative documented but not yet reviewed."
        if not narrative_ready else "Narrative reviewed or not yet documented.",
    }

    lcd_baseline = _get(form_data, "diagnoses", "lcdEligibilityNarrative")
    checks["lcdBaseline"] = {
        "label": "LCD evidence baseline available",
        "ready": _has_text(lcd_baseline),
        "message": "LCD eligibility support narrative is required." if not _has_text(lcd_baseline) else "LCD evidence baseline documented.",
    }

    referrals_reviewed = _get(form_data, "referrals", "reviewed") is True
    checks["referralsReviewed"] = {
        "label": "Referrals reviewed",
        "ready": referrals_reviewed,
        "message": "Referral status has not been marked reviewed." if not referrals_reviewed else "Referrals reviewed.",
    }

    poc_completeness = evaluate_poc_completeness(poc_problems)
    checks["pocCompleteness"] = {
        "label": "Goals, interventions & disciplines present",
        "ready": poc_completeness["ready"],
        "message": poc_completeness["message"],
        "incompleteLabels": poc_completeness["incomplete_labels"],
    }

    # --- HA Assignment -> CHHA Plan of Care must be finished before lock.
    # Only applies when a Home Health Aide is actually assigned (and the
    # HA Assignment card isn't marked N/A) -- a patient with no CHHA
    # involvement has nothing to complete here.
    ha_not_applicable = _get(form_data, "haAssignment", "notApplicable") is True
    ha_assigned_aide = _get(form_data, "haAssignment", "assignedAide")
    ha_assigned = (not ha_not_applicable) and _has_text(ha_assigned_aide)
    chha_poc_completed = _get(form_data, "chhaPoc", "completed") is True
    chha_poc_ready = (not ha_assigned) or chha_poc_completed
    checks["chhaPocCompleted"] = {
        "label": "CHHA Plan of Care completed",
        "ready": chha_poc_ready,
        "message": "A Home Health Aide is assigned but the CHHA Plan of Care has not been marked complete."
        if not chha_poc_ready else "CHHA Plan of Care completed (or no HA assigned).",
    }

    ready = all(check["ready"] for check in checks.values())
    return {"ready": ready, "checks": checks}
