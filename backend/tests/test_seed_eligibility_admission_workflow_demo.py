"""
Tests for scripts/seed_eligibility_admission_workflow_demo.py (Directive
Phase 10 -- synthetic data scenarios A-E). Exercises the script's `run()`
body directly against the isolated test database via the db_session
fixture, asserting each scenario lands in the correct state:

  A. Referral        -- no admission row, admission gate CLEAR (no rows
                         yet, non-regression rule), absent from the
                         billing readiness report.
  B. Admission Hold   -- admission gate ADMISSION_REVIEW_REQUIRED, absent
                         from the billing readiness report (not ADMITTED).
  C. Ready            -- present in the billing readiness report, READY,
                         admission gate CLEAR.
  D. At Risk          -- present, AT_RISK (late-NOE warning only, no
                         blockers), admission gate CLEAR.
  E. Not Ready        -- present, NOT_READY (missing certification
                         blocker), admission gate CLEAR.
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from scripts.seed_eligibility_admission_workflow_demo import run  # noqa: E402
from app.billing.services.readiness_workflow_service import derive_readiness_status  # noqa: E402


def test_scenario_a_referral_is_clear_and_excluded_from_billing(db_session):
    result = run(db_session)

    assert result["referral_admission_gate"].gate_status == "CLEAR"
    assert str(result["referral_patient"].id) not in result["by_patient"]


def test_scenario_b_admission_hold_requires_review_and_is_excluded_from_billing(db_session):
    result = run(db_session)

    assert result["hold_admission_gate"].gate_status == "ADMISSION_REVIEW_REQUIRED"
    assert len(result["hold_admission_gate"].blockers) == 2  # both eligibility AND benefit-period unresolved
    assert str(result["hold_patient"].id) not in result["by_patient"]


def test_scenario_c_ready(db_session):
    result = run(db_session)

    assert result["ready_admission_gate"].gate_status == "CLEAR"
    row = result["by_patient"][str(result["ready_patient"].id)]
    assert row["ready"] is True
    assert derive_readiness_status(blockers=row["blockers"], warnings=row["warnings"]) == "READY"


def test_scenario_d_at_risk(db_session):
    result = run(db_session)

    row = result["by_patient"][str(result["at_risk_patient"].id)]
    assert row["ready"] is True  # AT_RISK is still billable -- warnings, not blockers
    assert derive_readiness_status(blockers=row["blockers"], warnings=row["warnings"]) == "AT_RISK"
    assert len(row["warnings"]) >= 1
    assert len(row["blockers"]) == 0


def test_scenario_e_not_ready(db_session):
    result = run(db_session)

    row = result["by_patient"][str(result["not_ready_patient"].id)]
    assert row["ready"] is False
    assert derive_readiness_status(blockers=row["blockers"], warnings=row["warnings"]) == "NOT_READY"
    assert len(row["blockers"]) >= 1


def test_seed_is_idempotent(db_session):
    """Re-running must not fail or duplicate rows -- required for the
    script to be safely re-runnable in any local/dev database."""
    run(db_session)
    result = run(db_session)

    assert derive_readiness_status(
        blockers=result["by_patient"][str(result["ready_patient"].id)]["blockers"],
        warnings=result["by_patient"][str(result["ready_patient"].id)]["warnings"],
    ) == "READY"
