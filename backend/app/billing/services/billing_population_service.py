"""
Canonical billing-candidate population selector.

CORRECTIVE DIRECTIVE (Billing Population Correction, discovered during
worktree reconciliation, 2026-09-11): both `build_tenant_billing_readiness_report`
and `batch_generate_patient_billing` independently filtered on the
patient's *current* status (`patients.status = 'ACTIVE'`), which silently
drops a patient from all future billing consideration the moment they are
discharged, die, are revoked, or transfer out -- even though real,
never-billed hospice services they received *before* that event remain
legitimately billable (final-period claims, corrections, resubmissions).
That is a data-loss-shaped defect, not a feature: current census status
answers "is this patient receiving services today", not "is there
billable work remaining for this patient".

This module is the single, canonical replacement for that population
query. It answers a narrower, more correct question:

    "For this tenant and this service_date, which patients have an
    ADMITTED hospice episode whose window covers that service_date?"

An episode's window is [episode_start, episode_end]:
    - episode_start = COALESCE(effective_date, soc_date, admission_date)
    - episode_end   = discharged_at (NULL means the episode is still open)

IMPORTANT -- corrected 2026-09-13 with runtime evidence: `admissions.status`
is NOT a two-state ACTIVE/DISCHARGED vocabulary. There is a real,
currently-written 'ADMITTED' value: AdmissionGuardrailService
(app/services/admission/admission_guardrail_service.py,
trigger_admission_from_manual_soc(), invoked from the real
app/api/admission.py and app/api/admission_authorization.py routes)
auto-promotes an admission to status='ADMITTED' once clinical
prerequisites are satisfied (not training, election/consent signed,
records release signed, SOC datetime manually entered). This is a
distinct, *earlier*, clinical-readiness marker -- it does NOT yet
represent a financially/billing-active episode.

A separate, later, manual action -- the "activate admission" endpoint
in app/api/admissions.py -- is what transitions status to 'ACTIVE'
(financially recognized episode; the audit log even records this step
as action="PATIENT_ADMITTED", underscoring that 'ACTIVE' is the real
production term for a billing-relevant admitted episode). Discharge
(death, revocation, transfer, or ordinary discharge) always sets
status='DISCHARGED' with a `discharge_reason` describing which,
regardless of whether the episode was ever manually activated.

Full observed vocabulary: 'DRAFT' (server default; referral/pending,
never admitted) -> 'PENDING' / 'ADMITTED' (clinical guardrail states,
pre-financial-activation; see admission_guardrail_service.py) ->
'ACTIVE' (financially active, billable episode) -> 'DISCHARGED'
(closed episode, still billable for dates of service rendered before
discharge). This module intentionally gates the *billing* population on
'ACTIVE'/'DISCHARGED' only: a clinically-admitted-but-not-yet-activated
('ADMITTED'/'PENDING') episode has no recognized financial start date
and is not yet a billing candidate. origin/main's PR #84
readiness-report query filtered on `a.status = 'ADMITTED'`, which (per
the lifecycle above) matches only patients still awaiting financial
activation -- excluding every genuinely billable ACTIVE or DISCHARGED
episode, which is the real defect this module corrects.

Deliberately NOT part of this predicate (by design, see module docstring
of billing_readiness_service.py for why they stay separate concerns):
    - `patients.status` (current census state) -- never gates population.
    - benefit-period validity, election/consent, authorization, payer
      sequence -- those are per-patient *readiness* blockers/warnings
      evaluated by `check_patient_billing_readiness`, not population
      inclusion/exclusion. A patient with no benefit period on file is
      still a billing candidate; they simply come back NOT READY with a
      blocker explaining why.

Both `build_tenant_billing_readiness_report` (the readiness dashboard)
and `batch_generate_patient_billing` (the actual claim generator) must
call this same function so the two never silently diverge again.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

# Default general Medicare hospice timely-filing window: one calendar
# year (365 days) from the date of service. This is the *default* only --
# a payer-specific override (a real number of days on file for that
# payer/contract) must take precedence when one is configured. There is
# no payer-specific override source in this codebase yet (see
# billing_population_service module docstring / reconciliation report),
# so `payer_override_days` is accepted but always None today; wiring a
# real payer-rule source is tracked as follow-up work, not invented here.
DEFAULT_TIMELY_FILING_DAYS = 365


@dataclass(frozen=True)
class BillingCandidate:
    patient_id: str
    mrn: str
    admission_id: str
    episode_start: date
    episode_end: date | None


def select_billing_candidate_patients(
    db: Session,
    *,
    tenant_id: str,
    service_date: date,
) -> list[BillingCandidate]:
    """
    Returns every patient in `tenant_id` with an admission that was ever
    admitted (status ACTIVE or DISCHARGED -- never DRAFT/pending-referral)
    whose episode window covers `service_date`, regardless of the
    patient's *current* status. A patient discharged/deceased/revoked/
    transferred after `service_date` is still returned here if
    `service_date` falls inside their admitted episode -- their current
    status never excludes a service date that was legitimately billable
    when delivered.

    Pending-admission and referral-only records (admission status
    'DRAFT', or no admission row at all) are never returned -- there is
    no billable hospice episode to attribute a claim to.
    """
    rows = db.execute(
        text(
            """
            SELECT DISTINCT ON (p.id)
                p.id::text AS patient_id,
                p.mrn AS mrn,
                a.id::text AS admission_id,
                COALESCE(a.effective_date, a.soc_date, a.admission_date)::date AS episode_start,
                a.discharged_at::date AS episode_end
            FROM patients p
            JOIN admissions a
              ON a.tenant_id = p.tenant_id AND a.patient_id = p.id
            WHERE p.tenant_id = :tenant_id
              AND a.status IN ('ACTIVE', 'DISCHARGED')
              AND COALESCE(a.effective_date, a.soc_date, a.admission_date)::date <= :service_date
              AND (a.discharged_at IS NULL OR a.discharged_at::date >= :service_date)
            ORDER BY p.id, COALESCE(a.effective_date, a.soc_date, a.admission_date) DESC
            """
        ),
        {"tenant_id": tenant_id, "service_date": service_date},
    ).mappings().all()

    return [
        BillingCandidate(
            patient_id=row["patient_id"],
            mrn=row["mrn"],
            admission_id=row["admission_id"],
            episode_start=row["episode_start"],
            episode_end=row["episode_end"],
        )
        for row in rows
    ]


def compute_timely_filing_deadline(
    service_date: date,
    *,
    payer_override_days: int | None = None,
) -> date:
    """
    The date by which a claim for `service_date` must be filed.

    Uses `payer_override_days` when a caller supplies a real,
    payer-specific timely-filing window (e.g. from a future payer
    contract/rule source); otherwise falls back to the general Medicare
    hospice default of 365 days from the date of service. Never derives
    the deadline from the patient's discharge/death/revocation date --
    timely filing is a date-of-service and payer-rule concept, not a
    patient-status concept.
    """
    days = payer_override_days if payer_override_days is not None else DEFAULT_TIMELY_FILING_DAYS
    from datetime import timedelta

    return service_date + timedelta(days=days)
