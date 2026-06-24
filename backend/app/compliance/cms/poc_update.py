from __future__ import annotations

from datetime import timedelta, date, datetime
from uuid import UUID
from typing import Optional

from app.compliance.types import RuleMeta, Obligation


# =========================================================
# RULE METADATA
# =========================================================

RULE = RuleMeta(
    regulator="CMS",
    code="CMS-418.56-POC-UPDATE",
    title="Plan of Care update timing (ROUTINE vs CRISIS)",
    version="2026.05",
    effective_date="2026-05-23",
    reference="CMS Hospice CoPs §418.56",
    description=(
        "Defines timing and evidence requirements for POC updates. "
        "CRISIS visits trigger same-day completion; ROUTINE visits require "
        "supervisory RN anchoring for periodic scheduling."
    ),
)


# =========================================================
# NORMALIZATION HELPERS
# =========================================================

def _norm(value: Optional[str], default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip().upper()


def _safe_str(value) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def _safe_date(value) -> Optional[date]:
    """
    Normalize visit date safely.

    Accepts:
    - date
    - datetime

    Rejects everything else safely.
    """
    if value is None:
        return None

    if isinstance(value, date) and not isinstance(value, datetime):
        return value

    if isinstance(value, datetime):
        return value.date()

    return None


# =========================================================
# HELPER WRAPPERS (DEFENSIVE)
# =========================================================

def _is_rn_visit(visit, helpers) -> bool:
    try:
        visit_type = _norm(helpers._get_visit_type(visit))
    except Exception:
        return False

    return visit_type == "RN"


def _get_care_level(visit, helpers) -> str:
    try:
        return _norm(helpers._get_care_level(visit), default="ROUTINE")
    except Exception:
        return "ROUTINE"


def _is_supervisory(visit, helpers) -> bool:
    try:
        return bool(helpers._is_supervisory(visit))
    except Exception:
        return False


def _get_visit_date(visit, helpers) -> Optional[date]:
    try:
        raw = helpers._get_visit_date(visit)
    except Exception:
        return None

    return _safe_date(raw)


def _get_patient_id(visit, helpers):
    try:
        return _safe_str(helpers._get_patient_id(visit))
    except Exception:
        return None


def _get_visit_id(visit, helpers):
    try:
        return _safe_str(helpers._get_visit_id(visit))
    except Exception:
        return None


# =========================================================
# RULE EVALUATION
# =========================================================

def evaluate(
    *,
    visit,
    tenant_id: UUID,
    helpers,
    benefit_period_id=None,
):
    """
    CMS Hospice CoP §418.56 — Phase 1 Locked Enforcement

    CRISIS:
      - Any RN visit → same-day POC_UPDATE
      - Operational (MANUAL), not periodic

    ROUTINE:
      - ONLY supervisory RN visits may anchor PERIODIC POC updates
      - +14 days cadence

    Safety:
      - This function must NEVER emit a PERIODIC obligation from
        a non-supervisory RN visit.
    """

    # ---------------------------------------------------------
    # RN VALIDATION
    # ---------------------------------------------------------
    if not _is_rn_visit(visit, helpers):
        return None

    care_level = _get_care_level(visit, helpers)

    visit_date = _get_visit_date(visit, helpers)
    if visit_date is None:
        return None  # Hard fail-safe

    patient_id = _get_patient_id(visit, helpers)
    visit_id = _get_visit_id(visit, helpers)

    # ---------------------------------------------------------
    # CRISIS
    # ---------------------------------------------------------
    if care_level == "CRISIS":
        return Obligation(
            task_type="POC_UPDATE",
            origin="MANUAL",
            due_date=visit_date,
            evidence_required=("VISIT",),
            patient_id=patient_id,
            visit_id=visit_id,
            benefit_period_id=benefit_period_id,
            notes=(
                "[CMS-418.56] CRISIS RN visit → same-day POC update. "
                "anchor=VISIT; scheduling=NONE"
            ),
        )

    # ---------------------------------------------------------
    # ROUTINE
    # ---------------------------------------------------------
    if care_level == "ROUTINE":
        if not _is_supervisory(visit, helpers):
            return None  # 🚫 HARD STOP

        return Obligation(
            task_type="POC_UPDATE",
            origin="PERIODIC",
            due_date=visit_date + timedelta(days=14),
            evidence_required=("VISIT",),
            patient_id=patient_id,
            visit_id=visit_id,
            benefit_period_id=benefit_period_id,
            notes=(
                "[CMS-418.56] ROUTINE supervisory RN visit → POC update +14 days. "
                "anchor=SUPERVISORY_RN; interval=14d"
            ),
        )

    # ---------------------------------------------------------
    # ANY OTHER STATE
    # ---------------------------------------------------------
    return None