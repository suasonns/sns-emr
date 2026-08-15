# =========================================================
# FILE: app/services/poc_compiler_service.py
# PURPOSE: Plan of Care compiler
# STATUS: MINIMUM PRODUCTION-GRADE
# SOURCE OF TRUTH: plan_of_care_versions.snapshot_json
# =========================================================

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.plan_of_care import PlanOfCare
from app.models.plan_of_care_version import PlanOfCareVersion
from app.models.poc import POCProblem, POCGoal, POCIntervention

from app.services.poc_compiler_rn_mapper import map_rn_ica_to_problem_nodes

# =========================================================
# RESULT DTO
# =========================================================

@dataclass
class POCCompileResult:
    result: str  # "created_new_version" | "no_op"
    plan_of_care_id: UUID
    version_id: Optional[UUID]
    version_number: Optional[int]
    based_on_version_id: Optional[UUID]
    problem_count: int
    goal_count: int
    intervention_count: int
    snapshot_hash: str


# =========================================================
# PUBLIC ENTRYPOINT
# =========================================================

def compile_poc_from_ica(
    *,
    db: Session,
    tenant_id: UUID,
    plan_of_care_id: UUID,
    created_by_user_id: UUID,
    rn_ica_data: dict[str, Any],
    msw_ica_data: Optional[dict[str, Any]] = None,
    sc_ica_data: Optional[dict[str, Any]] = None,
    change_reason: str = "POC compiled from ICA",
    source_kind: str = "ICA",
    generated_from: Optional[dict[str, Any]] = None,
) -> POCCompileResult:
    """
    Minimum production-grade compiler flow:

    1. Load root POC + current version
    2. Build canonical snapshot from RN/MSW/SC inputs
    3. Compare snapshot with current version
    4. If unchanged -> no-op
    5. If changed -> create new version
    6. Rebuild projection tables from snapshot
    7. Supersede prior active version
    8. Update root current_version_id
    9. Assert snapshot/projection parity
    10. Commit once
    """
    poc = _load_plan_of_care_or_raise(
        db=db,
        tenant_id=tenant_id,
        plan_of_care_id=plan_of_care_id,
    )

    current_version = _get_current_version_or_none(
        db=db,
        tenant_id=tenant_id,
        poc=poc,
    )

    snapshot = _build_canonical_snapshot(
        db=db,
        rn_ica_data=rn_ica_data,
        msw_ica_data=msw_ica_data,
        sc_ica_data=sc_ica_data,
    )

    snapshot_hash = _hash_snapshot(snapshot)

    if current_version is not None:
        current_snapshot = current_version.snapshot_json or {}
        if _snapshots_are_semantically_equal(current_snapshot, snapshot):
            problem_count, goal_count, intervention_count = _count_snapshot_nodes(snapshot)
            return POCCompileResult(
                result="no_op",
                plan_of_care_id=poc.id,
                version_id=current_version.id,
                version_number=current_version.version_number,
                based_on_version_id=current_version.based_on_version_id,
                problem_count=problem_count,
                goal_count=goal_count,
                intervention_count=intervention_count,
                snapshot_hash=snapshot_hash,
            )

    next_version_number = _get_next_version_number(current_version)

    new_version = PlanOfCareVersion(
        tenant_id=tenant_id,
        plan_of_care_id=poc.id,
        version_number=next_version_number,
        status="ACTIVE",
        based_on_version_id=current_version.id if current_version else None,
        source_kind=source_kind,
        change_reason=change_reason,
        generated_from=generated_from or {},
        reviewed_in_idg=False,
        snapshot_json=copy.deepcopy(snapshot),
        created_by_user_id=created_by_user_id,
        updated_by_user_id=created_by_user_id,
    )

    try:
        db.add(new_version)
        db.flush()

        _rebuild_projection_for_version(
            db=db,
            tenant_id=tenant_id,
            poc_version_id=new_version.id,
            snapshot=snapshot,
            created_by_user_id=created_by_user_id,
        )

        if current_version is not None:
            current_version.status = "SUPERSEDED"
            current_version.updated_by_user_id = created_by_user_id

        poc.current_version_id = new_version.id
        poc.updated_by_user_id = created_by_user_id

        _assert_projection_matches_snapshot(
            db=db,
            poc_version_id=new_version.id,
            snapshot=snapshot,
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    problem_count, goal_count, intervention_count = _count_snapshot_nodes(snapshot)

    return POCCompileResult(
        result="created_new_version",
        plan_of_care_id=poc.id,
        version_id=new_version.id,
        version_number=new_version.version_number,
        based_on_version_id=new_version.based_on_version_id,
        problem_count=problem_count,
        goal_count=goal_count,
        intervention_count=intervention_count,
        snapshot_hash=snapshot_hash,
    )


# =========================================================
# SNAPSHOT BUILD
# =========================================================

def _build_canonical_snapshot(
    *,
    db: Session,
    rn_ica_data: dict[str, Any],
    msw_ica_data: Optional[dict[str, Any]],
    sc_ica_data: Optional[dict[str, Any]],
) -> dict[str, Any]:
    """
    Canonical snapshot shape:

    {
      "problems": [
        {
          "problem_code": "...",
          "label": "...",
          "description": "...",
          "severity": "...",
          "source_diagnosis_code": "...",
          "source_condition": "...",
          "diagnosis_context": "...",
          "rule_key": "...",
          "source_kind": "...",
          "status": "ACTIVE",
          "sort_order": 100,
          "goals": [
            {
              "goal_text": "...",
              "measurable_outcome": "...",
              "target_timeframe": "...",
              "source_kind": "...",
              "status": "ACTIVE",
              "sort_order": 100,
              "interventions": [
                {
                  "discipline": "RN",
                  "intervention_text": "...",
                  "frequency": "...",
                  "instructions": "...",
                  "source_kind": "...",
                  "status": "ACTIVE",
                  "sort_order": 100
                }
              ]
            }
          ]
        }
      ]
    }

    Current version:
    - RN ICA supported now
    - MSW and SC hooks are already wired for future use
    """
    rn_nodes = _extract_rn_problem_nodes(db, rn_ica_data)
    msw_nodes = _extract_msw_problem_nodes(msw_ica_data) if msw_ica_data else []
    sc_nodes = _extract_sc_problem_nodes(sc_ica_data) if sc_ica_data else []

    all_nodes = rn_nodes + msw_nodes + sc_nodes
    normalized = [_normalize_problem_node(p) for p in all_nodes]
    normalized.sort(key=_problem_sort_key)

    return {
        "problems": normalized,
    }


def _extract_rn_problem_nodes(db: Session, rn_ica_data: dict[str, Any]) -> list[dict[str, Any]]:
    return map_rn_ica_to_problem_nodes(db, rn_ica_data)

def _extract_msw_problem_nodes(msw_ica_data: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(msw_ica_data, dict):
        raise ValueError("MSW ICA payload must be a dictionary")

    if isinstance(msw_ica_data.get("problems"), list):
        return msw_ica_data["problems"]

    poc_content = msw_ica_data.get("poc_content")
    if isinstance(poc_content, dict) and isinstance(poc_content.get("problems"), list):
        return poc_content["problems"]

    return []


def _extract_sc_problem_nodes(sc_ica_data: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(sc_ica_data, dict):
        raise ValueError("SC ICA payload must be a dictionary")

    if isinstance(sc_ica_data.get("problems"), list):
        return sc_ica_data["problems"]

    poc_content = sc_ica_data.get("poc_content")
    if isinstance(poc_content, dict) and isinstance(poc_content.get("problems"), list):
        return poc_content["problems"]

    return []


# =========================================================
# NORMALIZATION / DETERMINISM
# =========================================================

def _normalize_problem_node(node: dict[str, Any]) -> dict[str, Any]:
    problem = {
        "problem_code": _clean_str(node.get("problem_code")),
        "label": _clean_str(node.get("label")),
        "description": _clean_optional_str(node.get("description")),
        "severity": _clean_str(node.get("severity") or "UNKNOWN"),
        "source_diagnosis_code": _clean_optional_str(node.get("source_diagnosis_code")),
        "source_condition": _clean_optional_str(node.get("source_condition")),
        "diagnosis_context": _clean_str(node.get("diagnosis_context") or "MANUAL"),
        "rule_key": _clean_optional_str(node.get("rule_key")),
        "source_kind": _clean_str(node.get("source_kind") or "RULE_GENERATED"),
        "status": _clean_str(node.get("status") or "ACTIVE"),
        "sort_order": _coerce_int(node.get("sort_order"), default=100),
        "goals": [],
    }

    raw_goals = node.get("goals") or []
    if not isinstance(raw_goals, list):
        raise ValueError("Problem goals must be a list")

    goals = [_normalize_goal_node(g) for g in raw_goals]
    goals.sort(key=_goal_sort_key)
    problem["goals"] = goals

    if not problem["problem_code"]:
        raise ValueError("Problem problem_code is required")
    if not problem["label"]:
        raise ValueError("Problem label is required")

    return problem


def _normalize_goal_node(node: dict[str, Any]) -> dict[str, Any]:
    goal = {
        "goal_text": _clean_str(node.get("goal_text")),
        "measurable_outcome": _clean_optional_str(node.get("measurable_outcome")),
        "target_timeframe": _clean_optional_str(node.get("target_timeframe")),
        "source_kind": _clean_str(node.get("source_kind") or "RULE_GENERATED"),
        "status": _clean_str(node.get("status") or "ACTIVE"),
        "sort_order": _coerce_int(node.get("sort_order"), default=100),
        "interventions": [],
    }

    raw_interventions = node.get("interventions") or []
    if not isinstance(raw_interventions, list):
        raise ValueError("Goal interventions must be a list")

    interventions = [_normalize_intervention_node(i) for i in raw_interventions]
    interventions.sort(key=_intervention_sort_key)
    goal["interventions"] = interventions

    if not goal["goal_text"]:
        raise ValueError("Goal goal_text is required")

    return goal


def _normalize_intervention_node(node: dict[str, Any]) -> dict[str, Any]:
    intervention = {
        "discipline": _clean_str(node.get("discipline")),
        "intervention_text": _clean_str(node.get("intervention_text")),
        "frequency": _clean_optional_str(node.get("frequency")),
        "instructions": _clean_optional_str(node.get("instructions")),
        "source_kind": _clean_str(node.get("source_kind") or "RULE_GENERATED"),
        "status": _clean_str(node.get("status") or "ACTIVE"),
        "sort_order": _coerce_int(node.get("sort_order"), default=100),
    }

    if not intervention["discipline"]:
        raise ValueError("Intervention discipline is required")
    if not intervention["intervention_text"]:
        raise ValueError("Intervention intervention_text is required")

    return intervention


def _problem_sort_key(problem: dict[str, Any]) -> tuple:
    return (
        problem.get("sort_order", 100),
        problem.get("problem_code") or "",
        problem.get("label") or "",
    )


def _goal_sort_key(goal: dict[str, Any]) -> tuple:
    return (
        goal.get("sort_order", 100),
        goal.get("goal_text") or "",
    )


def _intervention_sort_key(intervention: dict[str, Any]) -> tuple:
    return (
        intervention.get("sort_order", 100),
        intervention.get("discipline") or "",
        intervention.get("intervention_text") or "",
    )


def _clean_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _clean_optional_str(value: Any) -> Optional[str]:
    cleaned = _clean_str(value)
    return cleaned or None


def _coerce_int(value: Any, *, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except Exception:
        return default


# =========================================================
# SNAPSHOT COMPARISON
# =========================================================

def _hash_snapshot(snapshot: dict[str, Any]) -> str:
    canonical = _canonicalize_json(snapshot)
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _snapshots_are_semantically_equal(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return _hash_snapshot(left) == _hash_snapshot(right)


def _canonicalize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _canonicalize_json(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        return [_canonicalize_json(v) for v in value]
    return value


# =========================================================
# DB LOAD / VERSION FLOW
# =========================================================

def _load_plan_of_care_or_raise(
    *,
    db: Session,
    tenant_id: UUID,
    plan_of_care_id: UUID,
) -> PlanOfCare:
    poc = (
        db.query(PlanOfCare)
        .filter(
            PlanOfCare.id == plan_of_care_id,
            PlanOfCare.tenant_id == tenant_id,
        )
        .first()
    )
    if not poc:
        raise ValueError("Plan of Care not found in tenant")
    return poc


def _get_current_version_or_none(
    *,
    db: Session,
    tenant_id: UUID,
    poc: PlanOfCare,
) -> Optional[PlanOfCareVersion]:
    if poc.current_version_id:
        version = (
            db.query(PlanOfCareVersion)
            .filter(
                PlanOfCareVersion.id == poc.current_version_id,
                PlanOfCareVersion.plan_of_care_id == poc.id,
                PlanOfCareVersion.tenant_id == tenant_id,
            )
            .first()
        )
        if not version:
            raise ValueError("Current version pointer is invalid")
        return version

    existing_versions = (
        db.query(PlanOfCareVersion)
        .filter(
            PlanOfCareVersion.plan_of_care_id == poc.id,
            PlanOfCareVersion.tenant_id == tenant_id,
        )
        .count()
    )
    if existing_versions > 0:
        raise ValueError("Plan of Care has versions but no current_version_id")
    return None


def _get_next_version_number(current_version: Optional[PlanOfCareVersion]) -> int:
    if current_version is None:
        return 1
    return current_version.version_number + 1


# =========================================================
# PROJECTION REBUILD
# =========================================================

def _rebuild_projection_for_version(
    *,
    db: Session,
    tenant_id: UUID,
    poc_version_id: UUID,
    snapshot: dict[str, Any],
    created_by_user_id: UUID,
) -> None:
    problems = snapshot.get("problems") or []
    if not isinstance(problems, list):
        raise ValueError("Snapshot problems must be a list")

    for problem_node in problems:
        problem_row = POCProblem(
            tenant_id=tenant_id,
            poc_version_id=poc_version_id,
            source_diagnosis_code=problem_node.get("source_diagnosis_code"),
            source_condition=problem_node.get("source_condition"),
            diagnosis_context=problem_node.get("diagnosis_context") or "MANUAL",
            rule_key=problem_node.get("rule_key"),
            problem_code=problem_node["problem_code"],
            label=problem_node["label"],
            description=problem_node.get("description"),
            severity=problem_node.get("severity") or "UNKNOWN",
            source_kind=problem_node.get("source_kind") or "RULE_GENERATED",
            is_rule_generated=(problem_node.get("source_kind") or "RULE_GENERATED") == "RULE_GENERATED",
            status=problem_node.get("status") or "ACTIVE",
            sort_order=problem_node.get("sort_order") or 100,
            created_by_user_id=created_by_user_id,
            updated_by_user_id=created_by_user_id,
        )
        db.add(problem_row)
        db.flush()

        for goal_node in problem_node.get("goals", []):
            goal_row = POCGoal(
                tenant_id=tenant_id,
                problem_id=problem_row.id,
                goal_text=goal_node["goal_text"],
                measurable_outcome=goal_node.get("measurable_outcome"),
                target_timeframe=goal_node.get("target_timeframe"),
                source_kind=goal_node.get("source_kind") or "RULE_GENERATED",
                is_rule_generated=(goal_node.get("source_kind") or "RULE_GENERATED") == "RULE_GENERATED",
                status=goal_node.get("status") or "ACTIVE",
                sort_order=goal_node.get("sort_order") or 100,
                created_by_user_id=created_by_user_id,
                updated_by_user_id=created_by_user_id,
            )
            db.add(goal_row)
            db.flush()

            for intervention_node in goal_node.get("interventions", []):
                intervention_row = POCIntervention(
                    tenant_id=tenant_id,
                    goal_id=goal_row.id,
                    discipline=intervention_node["discipline"],
                    intervention_text=intervention_node["intervention_text"],
                    frequency=intervention_node.get("frequency"),
                    instructions=intervention_node.get("instructions"),
                    source_kind=intervention_node.get("source_kind") or "RULE_GENERATED",
                    is_rule_generated=(intervention_node.get("source_kind") or "RULE_GENERATED") == "RULE_GENERATED",
                    status=intervention_node.get("status") or "ACTIVE",
                    sort_order=intervention_node.get("sort_order") or 100,
                    created_by_user_id=created_by_user_id,
                    updated_by_user_id=created_by_user_id,
                )
                db.add(intervention_row)

    db.flush()


# =========================================================
# PARITY ASSERTS
# =========================================================

def _assert_projection_matches_snapshot(
    *,
    db: Session,
    poc_version_id: UUID,
    snapshot: dict[str, Any],
) -> None:
    expected_problem_count, expected_goal_count, expected_intervention_count = _count_snapshot_nodes(snapshot)

    actual_problem_count = (
        db.query(POCProblem)
        .filter(POCProblem.poc_version_id == poc_version_id)
        .count()
    )

    actual_goal_count = (
        db.query(POCGoal)
        .join(POCProblem, POCGoal.problem_id == POCProblem.id)
        .filter(POCProblem.poc_version_id == poc_version_id)
        .count()
    )

    actual_intervention_count = (
        db.query(POCIntervention)
        .join(POCGoal, POCIntervention.goal_id == POCGoal.id)
        .join(POCProblem, POCGoal.problem_id == POCProblem.id)
        .filter(POCProblem.poc_version_id == poc_version_id)
        .count()
    )

    if expected_problem_count != actual_problem_count:
        raise ValueError(
            f"Problem projection mismatch: expected {expected_problem_count}, got {actual_problem_count}"
        )

    if expected_goal_count != actual_goal_count:
        raise ValueError(
            f"Goal projection mismatch: expected {expected_goal_count}, got {actual_goal_count}"
        )

    if expected_intervention_count != actual_intervention_count:
        raise ValueError(
            f"Intervention projection mismatch: expected {expected_intervention_count}, got {actual_intervention_count}"
        )


def _count_snapshot_nodes(snapshot: dict[str, Any]) -> tuple[int, int, int]:
    problems = snapshot.get("problems") or []
    problem_count = len(problems)

    goal_count = 0
    intervention_count = 0

    for problem in problems:
        goals = problem.get("goals") or []
        goal_count += len(goals)

        for goal in goals:
            interventions = goal.get("interventions") or []
            intervention_count += len(interventions)

    return problem_count, goal_count, intervention_count