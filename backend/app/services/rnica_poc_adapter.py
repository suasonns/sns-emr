# app/services/rnica_poc_adapter.py
"""
RN ICA -> Plan of Care adapter.

This module is the ONLY bridge between the RN ICA JSONB assessment
(`RnicaAssessment.form_data`) and the authoritative Plan of Care document
model (`app.models.plan_of_care.PlanOfCare`,
`app.models.plan_of_care_version.PlanOfCareVersion`,
`app.models.poc.POCProblem/POCGoal/POCIntervention`) that already backs
`/plan-of-care/*` (`app.api.routes.plan_of_care`, `app.services.poc_service`).

There is deliberately NO second Plan of Care model here. Every RN ICA
"Add to POC / View POC / Update POC / Resolve POC" action, and the
existing (previously test-only) `generate_initial_poc_draft` engine, are
adapted onto the same versioned `poc_content = {"problems": [...]}"`
snapshot contract that `poc_service.create_plan_of_care` /
`poc_service.create_new_version` already validate and materialize.

Design rules (per SNS_RNICA_MASTER_MAP_1.1.md Master Sync Rules):
- Every write goes through `poc_service.create_new_version`, which
  supersedes the prior version and preserves it (full version history is
  never destroyed).
- Every RN-ICA-sourced problem carries a stable `rule_key` so re-running
  the auto-generator, or re-clicking "Add to POC", never creates a
  duplicate problem — it is matched, and only new evidence is merged in.
- Problems are identified across versions by `rule_key` (not by
  POCProblem.id), because `id` is re-minted every time a new version is
  materialized.
- `source_condition` is always `"RNICA:<section_key>"` and each problem's
  `description` always records the source RN ICA assessment id, section,
  and originating evidence text, so a Problem can always be traced back to
  the exact assessment/section/finding that produced it.
- Nothing here auto-creates a physician attestation
  (`create_physician_attestation` is always False) and nothing marks a
  version physician-approved. Physician sign-off remains a separate,
  explicit workflow (`poc_physician_approval`).
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.admission import Admission
from app.models.plan_of_care import PlanOfCare
from app.models.plan_of_care_version import PlanOfCareVersion
from app.models.poc import POCProblem
from app.models.rnica_assessment import RnicaAssessment
from app.models.user import User
from app.services.admission.admission_service import AdmissionService
from app.services.poc_generation_service import generate_initial_poc_draft
from app.services.poc_service import (
    create_new_version as _create_new_poc_version,
    create_plan_of_care as _create_plan_of_care,
    get_active_plan_of_care_version,
    get_plan_of_care_by_admission,
)

logger = logging.getLogger("sns_emr")

RNICA_SOURCE_CONDITION_PREFIX = "RNICA:"


class RnicaPocAdapterError(ValueError):
    """Raised for adapter-level validation failures (mapped to HTTP 400 by callers)."""


# =========================================================
# NOTE ADAPTER — makes RnicaAssessment.form_data readable by
# poc_generation_service.generate_initial_poc_draft(note), which only
# needs a duck-typed object exposing `.content` (+ optional id/patient_id/
# visit_id/form_key/note_type/discipline via getattr-with-default).
# =========================================================

class _RnicaNoteAdapter:
    def __init__(self, assessment: RnicaAssessment):
        form_data = assessment.form_data or {}
        # generate_initial_poc_draft reads content["observed_data"] and
        # content["assessment"]; RN ICA form_data serves as both, since it
        # already contains both objective findings and clinician
        # assessment fields in the same section objects.
        self.content: dict[str, Any] = {
            "observed_data": form_data,
            "assessment": form_data,
        }
        self.id = assessment.id
        self.patient_id = assessment.patient_id
        self.visit_id = assessment.visit_id
        self.form_key = "RNICA"
        self.note_type = "RNICA"
        self.discipline = "RN"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "problem"


def _make_rule_key(prefix: str, section_key: str, label: str) -> str:
    """Builds a stable, deterministic identity key for a Plan of Care
    problem that is guaranteed to fit `poc_problems.rule_key` (VARCHAR(50)).
    Same (prefix, section, label) always yields the same key, which is what
    duplicate-prevention on repeated "Add to POC" clicks relies on.
    """
    import hashlib

    digest = hashlib.sha1(label.strip().lower().encode("utf-8")).hexdigest()[:10]
    section_part = _slug(section_key)[:16]
    key = f"{prefix}_{section_part}_{digest}"
    return key[:50]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# =========================================================
# POC BOOTSTRAP / RESOLUTION
# =========================================================

def _resolve_admission(db: Session, *, tenant_id: UUID, patient_id: UUID) -> Admission:
    admission = AdmissionService.get_latest_admission(db=db, patient_id=patient_id, tenant_id=tenant_id)
    if not admission:
        raise RnicaPocAdapterError(
            "No admission exists for this patient yet; Plan of Care cannot be created until admission is established."
        )
    return admission


def _get_or_bootstrap_plan_of_care(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    admission_id: UUID,
    user_id: Optional[UUID],
) -> PlanOfCare:
    poc = get_plan_of_care_by_admission(db, tenant_id=tenant_id, admission_id=admission_id)
    if poc:
        return poc

    return _create_plan_of_care(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        admission_id=admission_id,
        created_by_user_id=user_id,
        poc_content={"problems": []},
        source_kind="ICA",
        change_reason="RN ICA: Plan of Care initialized",
        generated_from={"origin": "RNICA"},
        create_physician_attestation=False,
    )


def _current_snapshot(version: Optional[PlanOfCareVersion]) -> list[dict[str, Any]]:
    if not version or not isinstance(version.snapshot_json, dict):
        return []
    problems = version.snapshot_json.get("problems")
    return list(problems) if isinstance(problems, list) else []


# =========================================================
# PROBLEM DICT BUILDERS (POCProblemIn-compatible shape)
# =========================================================

def _build_manual_problem_dict(
    *,
    rnica_assessment_id: UUID,
    section_key: str,
    problem_label: str,
    evidence_text: str,
    goal_text: Optional[str],
    intervention_text: Optional[str],
    discipline: str,
) -> dict[str, Any]:
    rule_key = _make_rule_key("RNICA_MANUAL", section_key, problem_label)
    description = (
        f"Source: RN ICA assessment {rnica_assessment_id}, section '{section_key}'. "
        f"Finding: {evidence_text}"
    )
    goal_text = goal_text or f"Address: {problem_label}"
    goals: list[dict[str, Any]] = [
        {
            "goal_text": goal_text,
            "status": "ACTIVE",
            "source_kind": "RN_UPDATE",
            "interventions": (
                [
                    {
                        "discipline": discipline,
                        "intervention_text": intervention_text,
                        "status": "ACTIVE",
                        "source_kind": "RN_UPDATE",
                    }
                ]
                if intervention_text
                else []
            ),
        }
    ]

    return {
        "problem_code": rule_key,
        "label": problem_label,
        "description": description,
        "severity": "UNKNOWN",
        "source_condition": f"{RNICA_SOURCE_CONDITION_PREFIX}{section_key}",
        "diagnosis_context": "MANUAL",
        "rule_key": rule_key,
        "source_kind": "RN_UPDATE",
        "status": "ACTIVE",
        "goals": goals,
    }


def _map_generated_poc_item_to_problem_dict(
    item: dict[str, Any],
    *,
    rnica_assessment_id: UUID,
    section_key: str,
) -> dict[str, Any]:
    """Flattens a poc_generation_service `_poc_item(...)` result (nested
    problem/clinical_summary shape) into the flat POCProblemIn-compatible
    dict expected by poc_service._materialize_version_structure.
    """
    problem = item.get("problem") or {}
    clinical_summary = item.get("clinical_summary") or {}
    rule_key = str(item.get("poc_id") or f"AUTO_{section_key.upper()}")
    label = problem.get("label") or rule_key
    evidence = item.get("evidence") or []
    evidence_text = "; ".join(
        f"{e.get('source')}: {e.get('value')}" for e in evidence if isinstance(e, dict)
    ) or "auto-generated from RN ICA findings"

    description = (
        f"Source: RN ICA assessment {rnica_assessment_id}, section '{section_key}' "
        f"(auto-generated). Finding: {evidence_text}"
    )

    raw_goals = item.get("goals") or []
    raw_interventions = item.get("interventions") or []

    goals: list[dict[str, Any]] = []
    for g in raw_goals:
        if isinstance(g, dict):
            goals.append(
                {
                    "goal_text": g.get("goal_text") or label,
                    "status": g.get("status", "ACTIVE"),
                    "source_kind": "RULE_GENERATED",
                    "interventions": [],
                }
            )
    if not goals:
        goals = [{"goal_text": f"Address: {label}", "status": "ACTIVE", "source_kind": "RULE_GENERATED", "interventions": []}]

    # The generation engine emits interventions at problem level; the
    # authoritative schema hangs interventions off a goal, so they are
    # attached to the first goal (documented adapter behavior).
    for iv in raw_interventions:
        if isinstance(iv, dict):
            goals[0]["interventions"].append(
                {
                    "discipline": iv.get("discipline", "RN"),
                    "intervention_text": iv.get("intervention_text"),
                    "status": iv.get("status", "ACTIVE"),
                    "source_kind": "RULE_GENERATED",
                }
            )

    return {
        "problem_code": rule_key,
        "label": label,
        "description": description,
        "severity": str(clinical_summary.get("severity", "UNKNOWN")).upper(),
        "source_condition": f"{RNICA_SOURCE_CONDITION_PREFIX}{section_key}",
        "diagnosis_context": "MANUAL",
        "rule_key": rule_key,
        "source_kind": "RULE_GENERATED",
        "status": "ACTIVE",
        "goals": goals,
    }


# =========================================================
# READ / MUTATE the current active version's problem set
# =========================================================

def _find_index_by_rule_key(problems: list[dict[str, Any]], rule_key: str) -> Optional[int]:
    for idx, p in enumerate(problems):
        if p.get("rule_key") == rule_key:
            return idx
    return None


def _upsert_problems(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    user_id: Optional[UUID],
    new_problem_dicts: list[dict[str, Any]],
    change_reason: str,
    source_kind: str = "RN_UPDATE",
) -> dict[str, Any]:
    """Adds problems that don't already exist (matched by rule_key).
    Existing ACTIVE problems with the same rule_key are left untouched
    (their evidence/description is merged, never duplicated, never
    silently overwritten). Returns a small report dict.
    """
    admission = _resolve_admission(db, tenant_id=tenant_id, patient_id=patient_id)
    poc = _get_or_bootstrap_plan_of_care(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        admission_id=admission.id,
        user_id=user_id,
    )
    current_version = get_active_plan_of_care_version(db, tenant_id=tenant_id, plan_of_care_id=poc.id)
    problems = _current_snapshot(current_version)

    added: list[str] = []
    skipped_duplicate: list[str] = []
    merged: list[str] = []

    for candidate in new_problem_dicts:
        rule_key = candidate["rule_key"]
        existing_idx = _find_index_by_rule_key(problems, rule_key)
        if existing_idx is not None and problems[existing_idx].get("status") != "RESOLVED":
            # Duplicate prevention: never append a second row for the same
            # rule_key. Merge new evidence text into the existing
            # description so nothing is lost, but do not create a new
            # problem entry.
            existing_description = problems[existing_idx].get("description") or ""
            new_description = candidate.get("description") or ""
            if new_description and new_description not in existing_description:
                problems[existing_idx]["description"] = (
                    f"{existing_description}\n---\n{new_description}" if existing_description else new_description
                )
                merged.append(rule_key)
            skipped_duplicate.append(rule_key)
            continue

        problems.append(candidate)
        added.append(rule_key)

    if not added and not merged:
        # Nothing actually changed (pure repeat of an already-recorded
        # duplicate) — do not create a needless new version.
        return {
            "plan_of_care_id": poc.id,
            "version_id": current_version.id if current_version else None,
            "added": [],
            "skipped_duplicate": skipped_duplicate,
        }

    new_version = _create_new_poc_version(
        db,
        plan_of_care_id=poc.id,
        tenant_id=tenant_id,
        updated_content={"problems": problems},
        user_id=user_id,
        source_kind=source_kind,
        change_reason=change_reason,
        generated_from={"origin": "RNICA"},
        create_physician_attestation=False,
    )

    return {
        "plan_of_care_id": poc.id,
        "version_id": new_version.id,
        "version_number": new_version.version_number,
        "added": added,
        "skipped_duplicate": skipped_duplicate,
    }


def _mutate_problem(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    user_id: Optional[UUID],
    rule_key: str,
    change_reason: str,
    mutate_fn,
) -> dict[str, Any]:
    admission = _resolve_admission(db, tenant_id=tenant_id, patient_id=patient_id)
    poc = get_plan_of_care_by_admission(db, tenant_id=tenant_id, admission_id=admission.id)
    if not poc:
        raise RnicaPocAdapterError("No Plan of Care exists yet for this patient/admission.")

    current_version = get_active_plan_of_care_version(db, tenant_id=tenant_id, plan_of_care_id=poc.id)
    problems = _current_snapshot(current_version)

    idx = _find_index_by_rule_key(problems, rule_key)
    if idx is None:
        raise RnicaPocAdapterError(f"No Plan of Care problem found with rule_key={rule_key!r}.")

    mutate_fn(problems[idx])

    new_version = _create_new_poc_version(
        db,
        plan_of_care_id=poc.id,
        tenant_id=tenant_id,
        updated_content={"problems": problems},
        user_id=user_id,
        source_kind="RN_UPDATE",
        change_reason=change_reason,
        generated_from={"origin": "RNICA"},
        create_physician_attestation=False,
    )

    return {
        "plan_of_care_id": poc.id,
        "version_id": new_version.id,
        "version_number": new_version.version_number,
        "problem": problems[idx],
    }


# =========================================================
# PUBLIC API
# =========================================================

def add_manual_problem(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    user_id: Optional[UUID],
    rnica_assessment_id: UUID,
    section_key: str,
    problem_label: str,
    evidence_text: str,
    goal_text: Optional[str] = None,
    intervention_text: Optional[str] = None,
    discipline: str = "RN",
) -> dict[str, Any]:
    """'Add to POC' button handler for a single RN ICA body-system subcard."""
    problem_dict = _build_manual_problem_dict(
        rnica_assessment_id=rnica_assessment_id,
        section_key=section_key,
        problem_label=problem_label,
        evidence_text=evidence_text,
        goal_text=goal_text,
        intervention_text=intervention_text,
        discipline=discipline,
    )
    return _upsert_problems(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        user_id=user_id,
        new_problem_dicts=[problem_dict],
        change_reason=f"RN ICA: added problem from {section_key} section",
    )


def update_problem(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    user_id: Optional[UUID],
    section_key: str,
    rule_key: str,
    label: Optional[str] = None,
    description_addendum: Optional[str] = None,
    severity: Optional[str] = None,
) -> dict[str, Any]:
    """'Update POC' button handler. Patches an existing problem in place
    (new version, prior version preserved) — never renames/duplicates it.
    """

    def _patch(problem: dict[str, Any]) -> None:
        if label:
            problem["label"] = label
        if severity:
            problem["severity"] = severity.upper()
        if description_addendum:
            existing = problem.get("description") or ""
            problem["description"] = f"{existing}\n---\nUpdate: {description_addendum}" if existing else description_addendum

    return _mutate_problem(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        user_id=user_id,
        rule_key=rule_key,
        change_reason=f"RN ICA: updated problem in {section_key} section",
        mutate_fn=_patch,
    )


def resolve_problem(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    user_id: Optional[UUID],
    section_key: str,
    rule_key: str,
) -> dict[str, Any]:
    """'Resolve POC' button handler. Marks the problem RESOLVED (never
    deletes it) in a new version.
    """

    def _resolve(problem: dict[str, Any]) -> None:
        problem["status"] = "RESOLVED"
        for goal in problem.get("goals", []):
            if isinstance(goal, dict) and goal.get("status") == "ACTIVE":
                goal["status"] = "MET"

    return _mutate_problem(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        user_id=user_id,
        rule_key=rule_key,
        change_reason=f"RN ICA: resolved problem in {section_key} section",
        mutate_fn=_resolve,
    )


def deactivate_problem(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    user_id: Optional[UUID],
    section_key: str,
    rule_key: str,
) -> dict[str, Any]:
    """'Deactivate Problem' handler (SECTION 11 — Master Plan of Care
    Review). Distinct from `resolve_problem`: deactivation means the
    problem is no longer being actively tracked/reviewed (e.g. superseded
    by a later finding, or determined not clinically relevant), NOT that
    its goal was clinically met. Marks the problem HISTORICAL (never
    deletes it) in a new version.
    """

    def _deactivate(problem: dict[str, Any]) -> None:
        problem["status"] = "HISTORICAL"
        for goal in problem.get("goals", []):
            if isinstance(goal, dict) and goal.get("status") == "ACTIVE":
                goal["status"] = "HISTORICAL"

    return _mutate_problem(
        db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        user_id=user_id,
        rule_key=rule_key,
        change_reason=f"RN ICA: deactivated problem in {section_key} section",
        mutate_fn=_deactivate,
    )


def link_existing_problem(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    user_id: Optional[UUID],
    rnica_assessment_id: UUID,
    section_key: str,
    rule_key: str,
    evidence_text: str,
) -> dict[str, Any]:
    """SECTION 11.C — Master Plan of Care Review 'Link Existing Problem'.

    Attaches additional source evidence — documented in `section_key` — to
    an ALREADY-EXISTING Plan of Care problem, matched by its stable
    `rule_key`. This is the explicit, clinician-initiated counterpart to
    the automatic rule_key-match dedup in `_upsert_problems`: it lets a
    clinician deliberately say "this finding also supports a problem that
    was already documented elsewhere" without ever creating a second
    problem row for it.

    Guarantees:
    - No new POC storage: reuses the same versioned
      `poc_content = {"problems": [...]}` snapshot contract as every other
      adapter write (`poc_service.create_new_version`).
    - No duplicate problem creation: `rule_key` must already exist in the
      current active version; this function only ever mutates that one
      existing row, it never appends a new problem dict.
    - Origin metadata preserved: `source_condition` (and therefore
      `origin_section`) is never modified by linking — it always reflects
      where the problem was first documented.
    - Multiple evidence sources per problem: each link appends a
      structured entry (never overwrites/removes a prior one) to the
      problem's `evidence_sources` list, which round-trips through
      `PlanOfCareVersion.snapshot_json` the same way every other problem
      field already does.
    - Idempotent: re-linking identical evidence text from the same section
      is a no-op (no needless new version).
    """
    if not evidence_text or not evidence_text.strip():
        raise RnicaPocAdapterError("Evidence text is required to link an existing problem.")
    evidence_text = evidence_text.strip()

    admission = _resolve_admission(db, tenant_id=tenant_id, patient_id=patient_id)
    poc = get_plan_of_care_by_admission(db, tenant_id=tenant_id, admission_id=admission.id)
    if not poc:
        raise RnicaPocAdapterError("No Plan of Care exists yet for this patient/admission.")

    current_version = get_active_plan_of_care_version(db, tenant_id=tenant_id, plan_of_care_id=poc.id)
    problems = _current_snapshot(current_version)

    idx = _find_index_by_rule_key(problems, rule_key)
    if idx is None:
        raise RnicaPocAdapterError(f"No Plan of Care problem found with rule_key={rule_key!r}.")

    problem = problems[idx]
    existing_sources = problem.get("evidence_sources")
    existing_sources = list(existing_sources) if isinstance(existing_sources, list) else []

    already_linked = any(
        isinstance(s, dict) and s.get("section_key") == section_key and s.get("evidence_text") == evidence_text
        for s in existing_sources
    )
    if already_linked:
        # Identical evidence from this section is already recorded on this
        # problem — do not append a duplicate entry or create a needless
        # new version.
        return {
            "plan_of_care_id": poc.id,
            "version_id": current_version.id if current_version else None,
            "version_number": current_version.version_number if current_version else None,
            "problem": problem,
            "already_linked": True,
        }

    actor_name = _user_name_map(db, {user_id}).get(user_id) if user_id else None
    linked_at = _utcnow().isoformat()

    existing_sources.append(
        {
            "section_key": section_key,
            "rnica_assessment_id": str(rnica_assessment_id),
            "evidence_text": evidence_text,
            "linked_by_user_id": str(user_id) if user_id else None,
            "linked_by": actor_name,
            "linked_at": linked_at,
        }
    )
    problem["evidence_sources"] = existing_sources

    existing_description = problem.get("description") or ""
    addition = f"Linked from '{section_key}' section: {evidence_text}"
    if addition not in existing_description:
        problem["description"] = f"{existing_description}\n---\n{addition}" if existing_description else addition

    new_version = _create_new_poc_version(
        db,
        plan_of_care_id=poc.id,
        tenant_id=tenant_id,
        updated_content={"problems": problems},
        user_id=user_id,
        source_kind="RN_UPDATE",
        change_reason=f"RN ICA: linked existing problem to {section_key} section",
        generated_from={"origin": "RNICA"},
        create_physician_attestation=False,
    )

    return {
        "plan_of_care_id": poc.id,
        "version_id": new_version.id,
        "version_number": new_version.version_number,
        "problem": problem,
        "already_linked": False,
    }


def merge_duplicate_problems(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    user_id: Optional[UUID],
    surviving_rule_key: str,
    duplicate_rule_keys: list[str],
    merge_reason: str,
) -> dict[str, Any]:
    """SECTION 11 — Master Plan of Care Review 'Merge Duplicate Problems'.

    Consolidates one or more clinician-identified duplicate problems into a
    single surviving problem, matched by stable `rule_key`s. This is the
    explicit, clinician-initiated counterpart to the automatic rule_key-match
    dedup in `_upsert_problems`: it handles the case where two DIFFERENT
    rule_keys ended up documenting the same underlying clinical problem
    (e.g. raised from two different sections with different wording).

    Guarantees (per SNS_RNICA_MASTER_MAP_1.1.md Section 11 "Merge duplicate
    problems" / Master Sync Rule 4 -- "There is only ONE Problem ... for
    each problem. No duplicates."):
    - No new POC storage: reuses the same versioned
      `poc_content = {"problems": [...]}` snapshot contract as every other
      adapter write (`poc_service.create_new_version`).
    - Nothing is deleted. The duplicate's `POCProblem` row is marked
      `SUPERSEDED` (an existing, already-allowed status value -- no schema
      change) and carries a `merged_into_rule_key` pointer, so it remains
      fully visible to `View History` (SECTION 11.B) and to any audit
      reconstruction, it is just no longer surfaced as an active problem.
    - All of the duplicate's documented evidence is preserved: its
      `evidence_sources` are folded into the survivor's, and a structured
      `merged_from` entry (rule_key/label/description/who/when/reason) is
      appended to the survivor so the merge itself is traceable.
    - The survivor's own `origin_section`/`source_condition` (where IT was
      first documented) is never changed by merging another problem into
      it.
    - Idempotent per duplicate: a duplicate already marked SUPERSEDED with
      the same `merged_into_rule_key` is left alone (not re-merged, no
      needless new version) rather than erroring on a repeat request.
    """
    if not merge_reason or not merge_reason.strip():
        raise RnicaPocAdapterError("A reason is required to merge duplicate problems.")
    merge_reason = merge_reason.strip()

    duplicate_rule_keys = [k for k in dict.fromkeys(duplicate_rule_keys or []) if k]
    if not duplicate_rule_keys:
        raise RnicaPocAdapterError("At least one duplicate rule_key is required.")
    if surviving_rule_key in duplicate_rule_keys:
        raise RnicaPocAdapterError("The surviving problem cannot also be listed as a duplicate.")

    admission = _resolve_admission(db, tenant_id=tenant_id, patient_id=patient_id)
    poc = get_plan_of_care_by_admission(db, tenant_id=tenant_id, admission_id=admission.id)
    if not poc:
        raise RnicaPocAdapterError("No Plan of Care exists yet for this patient/admission.")

    current_version = get_active_plan_of_care_version(db, tenant_id=tenant_id, plan_of_care_id=poc.id)
    problems = _current_snapshot(current_version)

    survivor_idx = _find_index_by_rule_key(problems, surviving_rule_key)
    if survivor_idx is None:
        raise RnicaPocAdapterError(f"No Plan of Care problem found with rule_key={surviving_rule_key!r}.")
    survivor = problems[survivor_idx]

    actor_name = _user_name_map(db, {user_id}).get(user_id) if user_id else None
    merged_at = _utcnow().isoformat()

    survivor_evidence = survivor.get("evidence_sources")
    survivor_evidence = list(survivor_evidence) if isinstance(survivor_evidence, list) else []
    survivor_merged_from = survivor.get("merged_from")
    survivor_merged_from = list(survivor_merged_from) if isinstance(survivor_merged_from, list) else []

    already_merged: list[str] = []
    merged: list[str] = []
    changed = False

    for dup_rule_key in duplicate_rule_keys:
        dup_idx = _find_index_by_rule_key(problems, dup_rule_key)
        if dup_idx is None:
            raise RnicaPocAdapterError(f"No Plan of Care problem found with rule_key={dup_rule_key!r}.")
        duplicate = problems[dup_idx]

        if duplicate.get("status") == "SUPERSEDED" and duplicate.get("merged_into_rule_key") == surviving_rule_key:
            # Already merged into this exact survivor on a prior request —
            # no-op, do not re-fold evidence or create a needless version.
            already_merged.append(dup_rule_key)
            continue
        if duplicate.get("status") == "SUPERSEDED":
            raise RnicaPocAdapterError(
                f"Problem {dup_rule_key!r} has already been merged elsewhere and cannot be merged again."
            )

        # Fold the duplicate's linked evidence sources into the survivor's.
        dup_evidence = duplicate.get("evidence_sources")
        if isinstance(dup_evidence, list):
            for source in dup_evidence:
                if source not in survivor_evidence:
                    survivor_evidence.append(source)

        # Record the merge itself as a structured, traceable entry.
        survivor_merged_from.append(
            {
                "rule_key": dup_rule_key,
                "label": duplicate.get("label"),
                "origin_section": (
                    duplicate.get("source_condition", "").split(RNICA_SOURCE_CONDITION_PREFIX, 1)[-1]
                    if isinstance(duplicate.get("source_condition"), str)
                    and duplicate["source_condition"].startswith(RNICA_SOURCE_CONDITION_PREFIX)
                    else None
                ),
                "description": duplicate.get("description"),
                "merge_reason": merge_reason,
                "merged_by_user_id": str(user_id) if user_id else None,
                "merged_by": actor_name,
                "merged_at": merged_at,
            }
        )

        existing_description = survivor.get("description") or ""
        addition = f"Merged duplicate problem '{duplicate.get('label')}' ({dup_rule_key}): {duplicate.get('description') or ''}"
        if addition not in existing_description:
            survivor["description"] = f"{existing_description}\n---\n{addition}" if existing_description else addition

        duplicate["status"] = "SUPERSEDED"
        duplicate["merged_into_rule_key"] = surviving_rule_key
        for goal in duplicate.get("goals", []):
            if isinstance(goal, dict) and goal.get("status") == "ACTIVE":
                goal["status"] = "SUPERSEDED"
                for intervention in goal.get("interventions", []):
                    if isinstance(intervention, dict) and intervention.get("status") == "ACTIVE":
                        intervention["status"] = "SUPERSEDED"

        merged.append(dup_rule_key)
        changed = True

    survivor["evidence_sources"] = survivor_evidence
    survivor["merged_from"] = survivor_merged_from

    if not changed:
        return {
            "plan_of_care_id": poc.id,
            "version_id": current_version.id if current_version else None,
            "version_number": current_version.version_number if current_version else None,
            "survivor": survivor,
            "merged": [],
            "already_merged": already_merged,
        }

    new_version = _create_new_poc_version(
        db,
        plan_of_care_id=poc.id,
        tenant_id=tenant_id,
        updated_content={"problems": problems},
        user_id=user_id,
        source_kind="RN_UPDATE",
        change_reason=(
            f"RN ICA: merged duplicate problem(s) {', '.join(merged)} into {surviving_rule_key} ({merge_reason})"
        ),
        generated_from={"origin": "RNICA"},
        create_physician_attestation=False,
    )

    return {
        "plan_of_care_id": poc.id,
        "version_id": new_version.id,
        "version_number": new_version.version_number,
        "survivor": survivor,
        "merged": merged,
        "already_merged": already_merged,
    }


def _serialize_problem_row(
    row: POCProblem,
    *,
    evidence_sources: Optional[list[dict[str, Any]]] = None,
    merged_from: Optional[list[dict[str, Any]]] = None,
    merged_into_rule_key: Optional[str] = None,
) -> dict[str, Any]:
    """Shared read-model serializer for a materialized POCProblem row,
    used by both the per-section view (`list_section_problems`) and the
    cross-section Master Plan of Care Review (`list_all_problems`).

    `evidence_sources` (SECTION 11.C — Link Existing Problem) and
    `merged_from` / `merged_into_rule_key` (Merge Duplicate Problems) are
    optional because none of them are `POCProblem` SQL columns — they live
    in the current `PlanOfCareVersion.snapshot_json` problem dict (the same
    JSONB mechanism every problem is already round-tripped through) and are
    looked up separately by the caller. `origin_section` (parsed from
    `source_condition`) always reflects where the problem was *first*
    documented and is never changed by linking or by having another
    problem merged into it.
    """
    origin_section = None
    if row.source_condition and row.source_condition.startswith(RNICA_SOURCE_CONDITION_PREFIX):
        origin_section = row.source_condition[len(RNICA_SOURCE_CONDITION_PREFIX):]

    return {
        "rule_key": row.rule_key,
        "problem_code": row.problem_code,
        "label": row.label,
        "description": row.description,
        "severity": row.severity,
        "status": row.status,
        "source_kind": row.source_kind,
        "source_condition": row.source_condition,
        "origin_section": origin_section,
        "evidence_sources": evidence_sources or [],
        "merged_from": merged_from or [],
        "merged_into_rule_key": merged_into_rule_key,
        "goals": [
            {
                "goal_text": g.goal_text,
                "status": g.status,
                "interventions": [
                    {
                        "discipline": i.discipline,
                        "intervention_text": i.intervention_text,
                        "frequency": i.frequency,
                        "status": i.status,
                    }
                    for i in g.interventions
                ],
            }
            for g in row.goals
        ],
    }


def _snapshot_extras_by_rule_key(db: Session, *, tenant_id: UUID, version_id: Optional[UUID]) -> dict[str, dict[str, Any]]:
    """Read-side helper for problem fields that live only in the current
    version's `snapshot_json` problem dicts, not as `POCProblem` SQL
    columns: `evidence_sources` (SECTION 11.C — Link Existing Problem) and
    `merged_from` / `merged_into_rule_key` (Merge Duplicate Problems). Both
    round-trip through `PlanOfCareVersion.snapshot_json` the same way every
    other problem field already does, so they must be looked up separately
    and merged into the read model rather than read off the ORM row.
    """
    if not version_id:
        return {}
    version = (
        db.query(PlanOfCareVersion)
        .filter(PlanOfCareVersion.id == version_id, PlanOfCareVersion.tenant_id == tenant_id)
        .first()
    )
    if not version:
        return {}
    out: dict[str, dict[str, Any]] = {}
    for problem in _current_snapshot(version):
        rule_key = problem.get("rule_key")
        if not rule_key:
            continue
        sources = problem.get("evidence_sources")
        merged_from = problem.get("merged_from")
        out[rule_key] = {
            "evidence_sources": sources if isinstance(sources, list) else [],
            "merged_from": merged_from if isinstance(merged_from, list) else [],
            "merged_into_rule_key": problem.get("merged_into_rule_key"),
        }
    return out


def list_section_problems(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    section_key: str,
) -> list[dict[str, Any]]:
    """'View POC' button handler — returns materialized POCProblem rows
    (with goals/interventions) for the current active version, scoped to
    this RN ICA section.
    """
    admission = AdmissionService.get_latest_admission(db=db, patient_id=patient_id, tenant_id=tenant_id)
    if not admission:
        return []

    poc = get_plan_of_care_by_admission(db, tenant_id=tenant_id, admission_id=admission.id)
    if not poc or not poc.current_version_id:
        return []

    source_condition = f"{RNICA_SOURCE_CONDITION_PREFIX}{section_key}"
    rows = (
        db.query(POCProblem)
        .filter(
            POCProblem.tenant_id == tenant_id,
            POCProblem.poc_version_id == poc.current_version_id,
            POCProblem.source_condition == source_condition,
        )
        .order_by(POCProblem.sort_order)
        .all()
    )

    extras_by_rule_key = _snapshot_extras_by_rule_key(db, tenant_id=tenant_id, version_id=poc.current_version_id)
    return [
        _serialize_problem_row(
            row,
            evidence_sources=extras_by_rule_key.get(row.rule_key, {}).get("evidence_sources"),
            merged_from=extras_by_rule_key.get(row.rule_key, {}).get("merged_from"),
            merged_into_rule_key=extras_by_rule_key.get(row.rule_key, {}).get("merged_into_rule_key"),
        )
        for row in rows
    ]


def list_all_problems(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
) -> list[dict[str, Any]]:
    """SECTION 11 — Master Plan of Care Review. Returns every RN-ICA-sourced
    problem (any originating section) for the current active POC version,
    each carrying its `origin_section` (parsed from `source_condition`) so
    the review screen can display "Origin Section" without re-deriving it.

    This is a read-only synchronization/governance view over the same
    authoritative `poc_problems` rows that `list_section_problems` reads —
    it does not introduce a second Plan of Care store, and it never creates
    problems.
    """
    admission = AdmissionService.get_latest_admission(db=db, patient_id=patient_id, tenant_id=tenant_id)
    if not admission:
        return []

    poc = get_plan_of_care_by_admission(db, tenant_id=tenant_id, admission_id=admission.id)
    if not poc or not poc.current_version_id:
        return []

    rows = (
        db.query(POCProblem)
        .filter(
            POCProblem.tenant_id == tenant_id,
            POCProblem.poc_version_id == poc.current_version_id,
            POCProblem.source_condition.like(f"{RNICA_SOURCE_CONDITION_PREFIX}%"),
        )
        .order_by(POCProblem.sort_order)
        .all()
    )

    extras_by_rule_key = _snapshot_extras_by_rule_key(db, tenant_id=tenant_id, version_id=poc.current_version_id)
    return [
        _serialize_problem_row(
            row,
            evidence_sources=extras_by_rule_key.get(row.rule_key, {}).get("evidence_sources"),
            merged_from=extras_by_rule_key.get(row.rule_key, {}).get("merged_from"),
            merged_into_rule_key=extras_by_rule_key.get(row.rule_key, {}).get("merged_into_rule_key"),
        )
        for row in rows
    ]


def _user_name_map(db: Session, user_ids: set) -> dict:
    """Batch-resolve user ids -> display name for audit-trail attribution
    (same pattern as app/api/physician_orders.py::_user_name_map)."""
    ids = {uid for uid in user_ids if uid}
    if not ids:
        return {}
    rows = db.query(User.id, User.full_name, User.display_name).filter(User.id.in_(ids)).all()
    return {row[0]: (row[2] or row[1] or "Unknown") for row in rows}


def get_problem_history(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    rule_key: str,
) -> dict[str, Any]:
    """SECTION 11.B — Master Plan of Care Review 'View History'.

    Read-only governance view. Reconstructs a single problem's full
    lifecycle (created, last updated, status transitions, resolve events,
    deactivate events) entirely from metadata that already exists — no new
    audit table, no new storage.

    Every Plan of Care mutation (`poc_service.create_new_version`) fully
    re-materializes *every* still-present problem into the new version's
    `poc_problems` rows, each row stamped with that version's actor and
    timestamp (see `poc_service._materialize_version_structure`). So the
    ordered sequence of `PlanOfCareVersion` rows for a `rule_key` — and
    whether the problem's own fields differ between consecutive versions —
    already *is* the audit trail of what changed, when, and by whom;
    `PlanOfCareVersion.change_reason` records why (e.g. "RN ICA: resolved
    problem in skin section").
    """
    admission = AdmissionService.get_latest_admission(db=db, patient_id=patient_id, tenant_id=tenant_id)
    if not admission:
        raise RnicaPocAdapterError("No admission exists for this patient yet.")

    poc = get_plan_of_care_by_admission(db, tenant_id=tenant_id, admission_id=admission.id)
    if not poc:
        raise RnicaPocAdapterError("No Plan of Care exists yet for this patient/admission.")

    versions = (
        db.query(PlanOfCareVersion)
        .filter(
            PlanOfCareVersion.tenant_id == tenant_id,
            PlanOfCareVersion.plan_of_care_id == poc.id,
        )
        .order_by(PlanOfCareVersion.version_number.asc())
        .all()
    )
    if not versions:
        raise RnicaPocAdapterError("No Plan of Care versions exist yet for this patient/admission.")

    version_ids = [v.id for v in versions]
    problem_rows = (
        db.query(POCProblem)
        .filter(
            POCProblem.tenant_id == tenant_id,
            POCProblem.poc_version_id.in_(version_ids),
            POCProblem.rule_key == rule_key,
        )
        .all()
    )
    rows_by_version_id = {row.poc_version_id: row for row in problem_rows}

    # Chronological sequence of (version, problem-row-as-of-that-version),
    # skipping versions where this problem did not yet exist / no longer
    # appears in the snapshot.
    timeline = [(v, rows_by_version_id[v.id]) for v in versions if v.id in rows_by_version_id]
    if not timeline:
        raise RnicaPocAdapterError(f"No Plan of Care problem found with rule_key={rule_key!r}.")

    name_map = _user_name_map(db, {v.created_by_user_id for v, _ in timeline})

    def _actor(version: PlanOfCareVersion) -> str:
        return name_map.get(version.created_by_user_id, "Unknown")

    def _at(version: PlanOfCareVersion) -> Optional[str]:
        return version.created_at.isoformat() if version.created_at else None

    first_version, _first_row = timeline[0]
    _last_version, last_row = timeline[-1]

    status_changes: list[dict[str, Any]] = []
    last_changed_version = first_version
    prev_row: Optional[POCProblem] = None
    for version, row in timeline:
        if prev_row is not None:
            if row.status != prev_row.status:
                status_changes.append(
                    {
                        "versionNumber": version.version_number,
                        "changedAt": _at(version),
                        "changedBy": _actor(version),
                        "fromStatus": prev_row.status,
                        "toStatus": row.status,
                        "changeReason": version.change_reason,
                    }
                )
            if (
                row.status != prev_row.status
                or row.severity != prev_row.severity
                or row.label != prev_row.label
                or row.description != prev_row.description
            ):
                last_changed_version = version
        prev_row = row

    return {
        "ruleKey": rule_key,
        "problemCode": last_row.problem_code,
        "label": last_row.label,
        "currentStatus": last_row.status,
        "createdBy": _actor(first_version),
        "createdDate": _at(first_version),
        "lastUpdatedBy": _actor(last_changed_version),
        "lastUpdatedDate": _at(last_changed_version),
        "statusChanges": status_changes,
        "resolveEvents": [c for c in status_changes if c["toStatus"] == "RESOLVED"],
        "deactivateEvents": [c for c in status_changes if c["toStatus"] == "HISTORICAL"],
        "mergeEvents": [c for c in status_changes if c["toStatus"] == "SUPERSEDED"],
    }


def _payload_matches_authoritative_model(draft: dict[str, Any]) -> bool:
    """Confirms generate_initial_poc_draft's output shape is still the one
    this adapter maps (item.problem.code/label, item.clinical_summary.severity,
    item.goals[], item.interventions[], item.evidence[]) before it is ever
    applied to the live Plan of Care. If the shape drifts, we refuse to
    apply it rather than silently writing malformed problems.
    """
    if not isinstance(draft, dict) or "pocs" not in draft:
        return False
    for item in draft.get("pocs", []):
        if not isinstance(item, dict):
            return False
        if "problem" not in item or not isinstance(item.get("problem"), dict):
            return False
        if "code" not in item["problem"] or "label" not in item["problem"]:
            return False
    return True


def generate_and_apply_poc_from_assessment(
    db: Session,
    *,
    tenant_id: Optional[UUID],
    user_id: Optional[UUID],
    assessment: RnicaAssessment,
) -> dict[str, Any]:
    """Wires the existing `poc_generation_service.generate_initial_poc_draft`
    engine into the live RN ICA finalize/lock workflow.

    - Confirms the generator's payload shape matches the authoritative POC
      model before applying anything.
    - Applies via the same `_upsert_problems` path as manual Add-to-POC, so
      duplicate rule_keys are matched/merged rather than duplicated, and no
      existing problem or prior version is overwritten.
    - Never finalizes/attests — output remains DRAFT/ACTIVE, clinician review
      required, per Master Sync Rules.
    """
    if tenant_id is None:
        return {"applied": False, "reason": "missing_tenant_id"}

    note = _RnicaNoteAdapter(assessment)
    try:
        draft = generate_initial_poc_draft(note)
    except Exception:
        logger.exception(
            "RNICA_POC_GENERATION_FAILED assessment_id=%s patient_id=%s",
            str(assessment.id),
            str(assessment.patient_id),
        )
        return {"applied": False, "reason": "generation_error"}

    if not _payload_matches_authoritative_model(draft):
        logger.warning(
            "RNICA_POC_GENERATION_SHAPE_MISMATCH assessment_id=%s — refusing to apply, generator output does not match POCProblemIn contract",
            str(assessment.id),
        )
        return {"applied": False, "reason": "shape_mismatch"}

    pocs = draft.get("pocs", [])
    if not pocs:
        return {"applied": True, "added": [], "skipped_duplicate": [], "reason": "no_findings"}

    problem_dicts = [
        _map_generated_poc_item_to_problem_dict(
            item,
            rnica_assessment_id=assessment.id,
            section_key="rnica_auto",
        )
        for item in pocs
    ]

    try:
        result = _upsert_problems(
            db,
            tenant_id=tenant_id,
            patient_id=assessment.patient_id,
            user_id=user_id,
            new_problem_dicts=problem_dicts,
            change_reason="RN ICA finalized: auto-generated POC draft applied",
            source_kind="RULE_GENERATED",
        )
    except RnicaPocAdapterError as e:
        logger.warning(
            "RNICA_POC_GENERATION_NOT_APPLIED assessment_id=%s reason=%s",
            str(assessment.id),
            str(e),
        )
        return {"applied": False, "reason": str(e)}

    result["applied"] = True
    return result
