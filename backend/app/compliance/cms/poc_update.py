from __future__ import annotations

import yaml
from datetime import datetime, date, time, timedelta, UTC
from pathlib import Path
from typing import Any, List, Optional
from uuid import UUID

from app.compliance.types import RuleMeta, Obligation


RULE = RuleMeta(
    regulator="CMS",
    code="CMS-418.56-POC-UPDATE",
    title="Plan of Care update timing (ROUTINE vs CRISIS)",
    version="2026.05",
    effective_date=date(2026, 5, 23),
    reference="CMS Hospice CoPs §418.56",
    description=(
        "Defines timing and evidence requirements for POC updates. "
        "CRISIS visits trigger same-day completion; ROUTINE visits use "
        "configurable supervisory RN anchoring."
    ),
)

RULES = [RULE]


def get_rules() -> List[RuleMeta]:
    return RULES


def _load_config() -> dict:
    config_path = Path(__file__).resolve().parent / "cms_rules.yaml"

    if not config_path.exists():
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}


def _rule_config() -> dict:
    config = _load_config()
    rules = config.get("rules", {})
    if not isinstance(rules, dict):
        return {}
    return rules.get("poc_update_timing", {}) or {}


def _norm(value: Optional[str], default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip().upper()


def _safe_date(value: Any) -> Optional[date]:
    if value is None:
        return None

    if isinstance(value, date) and not isinstance(value, datetime):
        return value

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return None

    return None


def _get_visit_type(visit: Any, helpers: Any) -> str:
    try:
        return _norm(helpers._get_visit_type(visit))
    except Exception:
        return ""


def _get_care_level(visit: Any, helpers: Any) -> str:
    try:
        return _norm(helpers._get_care_level(visit), default="ROUTINE")
    except Exception:
        return "ROUTINE"


def _is_supervisory(visit: Any, helpers: Any) -> bool:
    try:
        return bool(helpers._is_supervisory(visit))
    except Exception:
        return False


def _get_visit_date(visit: Any, helpers: Any) -> Optional[date]:
    try:
        raw = helpers._get_visit_date(visit)
    except Exception:
        return None
    return _safe_date(raw)


def _get_patient_id(visit: Any, helpers: Any) -> Optional[UUID]:
    try:
        raw = helpers._get_patient_id(visit)
    except Exception:
        return None

    if raw is None:
        return None

    try:
        return raw if isinstance(raw, UUID) else UUID(str(raw))
    except Exception:
        return None


def _get_visit_id(visit: Any, helpers: Any) -> Optional[UUID]:
    try:
        raw = helpers._get_visit_id(visit)
    except Exception:
        return None

    if raw is None:
        return None

    try:
        return raw if isinstance(raw, UUID) else UUID(str(raw))
    except Exception:
        return None


def _is_rn_visit(visit: Any, helpers: Any) -> bool:
    return _get_visit_type(visit, helpers) == "RN"


def _end_of_day(value: date) -> datetime:
    return datetime.combine(value, time(23, 59, 59, tzinfo=UTC))


def evaluate(
    *,
    visit: Any,
    tenant_id: UUID,
    helpers: Any,
    benefit_period_id: Optional[UUID] = None,
    **_: Any,
) -> List[Obligation]:
    """
    CMS Hospice CoP-aligned POC update rule.

    Returns obligations only.
    No DB writes happen here.
    """

    config = _rule_config()
    if not config.get("enabled", True):
        return []

    patient_id = _get_patient_id(visit, helpers)
    if patient_id is None:
        return []

    if not _is_rn_visit(visit, helpers):
        return []

    visit_id = _get_visit_id(visit, helpers)
    visit_date = _get_visit_date(visit, helpers) or datetime.now(UTC).date()
    care_level = _get_care_level(visit, helpers)
    supervisory = _is_supervisory(visit, helpers)

    now = datetime.now(UTC)
    obligations: List[Obligation] = []

    crisis_same_day = bool(config.get("crisis_same_day", True))
    routine_supervisory_due_days = int(config.get("routine_supervisory_due_days", 14))

    if care_level == "CRISIS":
        due_date = _end_of_day(visit_date) if crisis_same_day else now
        obligations.append(
            Obligation(
                rule_code=RULE.code,
                regulator=RULE.regulator,
                task_type="POC_UPDATE",
                origin="rule_engine.cms.poc_update",
                created_at=now,
                due_date=due_date,
                evidence_required=("NOTE", "VISIT"),
                patient_id=patient_id,
                tenant_id=tenant_id,
                visit_id=visit_id,
                benefit_period_id=benefit_period_id,
                notes="CRISIS RN visit requires same-day plan-of-care update follow-up.",
            )
        )
        return obligations

    if care_level == "ROUTINE" and supervisory:
        due_date = _end_of_day(visit_date + timedelta(days=routine_supervisory_due_days))
        obligations.append(
            Obligation(
                rule_code=RULE.code,
                regulator=RULE.regulator,
                task_type="POC_UPDATE",
                origin="rule_engine.cms.poc_update",
                created_at=now,
                due_date=due_date,
                evidence_required=("NOTE", "VISIT"),
                patient_id=patient_id,
                tenant_id=tenant_id,
                visit_id=visit_id,
                benefit_period_id=benefit_period_id,
                notes=(
                    "ROUTINE supervisory RN visit anchored a configurable plan-of-care update "
                    f"window of {routine_supervisory_due_days} days."
                ),
            )
        )

    return obligations