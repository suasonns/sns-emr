from __future__ import annotations

"""
Real CMS Election Statement Addendum timeliness rule (42 CFR 418.24(b),
CMS Hospice CoPs / Transmittal 10573 and successors):

  - If the addendum is requested within the first 5 days of the hospice
    election, the hospice must furnish it in writing within 5 days of
    the request.
  - If requested after the first 5 days of the election (any time during
    the course of care), the hospice must furnish it within 3 days
    (72 hours) of the request -- regardless of who requested it (patient/
    representative, non-hospice provider, or a Medicare contractor).
  - If the patient dies, revokes the election, or is discharged before
    the applicable deadline elapses and the addendum has not yet been
    furnished, the requirement is considered satisfied (no addendum is
    owed).

This module only evaluates real, already-captured dates (election date,
request date, delivery date, discharge/death date) -- it never fabricates
a delivery or invents a request that wasn't logged.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import uuid

WITHIN_ELECTION_WINDOW_DAYS = 5
STANDARD_FURNISH_DEADLINE_DAYS = 5
EXPEDITED_FURNISH_DEADLINE_DAYS = 3

# CMS-1851-F / FY2027 Hospice Final Rule: for elections beginning on or
# after this date, the addendum is mandatory for every Medicare election
# regardless of request (see compute_mandatory_addendum_requirement below).
# This does not change or remove the pre-existing request-triggered rule
# (compute_addendum_compliance above), which still governs elections
# before this date and any post-request handling that still applies.
MANDATORY_ADDENDUM_RULE_EFFECTIVE_DATE = date(2026, 10, 1)
MANDATORY_INITIAL_FURNISH_DEADLINE_DAYS = 5
MANDATORY_POC_CHANGE_UPDATE_DEADLINE_DAYS = 3


class ElectionAddendumComplianceError(RuntimeError):
    pass


@dataclass(frozen=True)
class ElectionAddendumComplianceResult:
    deadline_days: int
    deadline_date: date
    is_satisfied: bool
    is_late: bool
    is_waived_by_early_discharge: bool
    reason: str | None


def compute_addendum_compliance(
    *,
    election_date: date,
    requested_date: date,
    delivered_date: date | None,
    discharge_or_death_date: date | None = None,
    not_required_reason: str | None = None,
    as_of_date: date | None = None,
) -> ElectionAddendumComplianceResult:
    """
    Args:
        election_date: the patient's real hospice election effective date.
        requested_date: the real date the addendum was requested.
        delivered_date: the real date the addendum was actually furnished
            in writing, or None if not yet furnished.
        discharge_or_death_date: the patient's real discharge_date when
            status indicates death/revocation/discharge (see
            sia_service.get_date_of_death for the same convention this
            app uses -- there is no dedicated date_of_death field).
        not_required_reason: a documented reason the requirement doesn't
            apply (e.g. request later withdrawn) -- must be a real,
            documented justification, never assumed.
        as_of_date: evaluation date for a still-undelivered addendum
            (defaults to today).
    """
    if election_date is None:
        raise ElectionAddendumComplianceError("election_date is required")
    if requested_date is None:
        raise ElectionAddendumComplianceError("requested_date is required")

    within_election_window = (requested_date - election_date).days <= WITHIN_ELECTION_WINDOW_DAYS
    deadline_days = STANDARD_FURNISH_DEADLINE_DAYS if within_election_window else EXPEDITED_FURNISH_DEADLINE_DAYS
    deadline_date = requested_date + timedelta(days=deadline_days)

    if not_required_reason:
        return ElectionAddendumComplianceResult(
            deadline_days=deadline_days,
            deadline_date=deadline_date,
            is_satisfied=True,
            is_late=False,
            is_waived_by_early_discharge=False,
            reason=f"Requirement waived: {not_required_reason}",
        )

    if delivered_date is not None:
        is_late = delivered_date > deadline_date
        return ElectionAddendumComplianceResult(
            deadline_days=deadline_days,
            deadline_date=deadline_date,
            is_satisfied=True,
            is_late=is_late,
            is_waived_by_early_discharge=False,
            reason=(
                f"Furnished {delivered_date.isoformat()}, after the "
                f"{deadline_days}-day deadline ({deadline_date.isoformat()})"
                if is_late
                else None
            ),
        )

    # Not yet delivered.
    if discharge_or_death_date is not None and discharge_or_death_date <= deadline_date:
        return ElectionAddendumComplianceResult(
            deadline_days=deadline_days,
            deadline_date=deadline_date,
            is_satisfied=True,
            is_late=False,
            is_waived_by_early_discharge=True,
            reason=(
                f"Requirement satisfied: patient discharged/revoked/died "
                f"{discharge_or_death_date.isoformat()}, before the "
                f"{deadline_days}-day deadline ({deadline_date.isoformat()}) elapsed"
            ),
        )

    evaluation_date = as_of_date or date.today()
    if evaluation_date <= deadline_date:
        return ElectionAddendumComplianceResult(
            deadline_days=deadline_days,
            deadline_date=deadline_date,
            is_satisfied=False,
            is_late=False,
            is_waived_by_early_discharge=False,
            reason=None,
        )

    return ElectionAddendumComplianceResult(
        deadline_days=deadline_days,
        deadline_date=deadline_date,
        is_satisfied=False,
        is_late=True,
        is_waived_by_early_discharge=False,
        reason=(
            f"Election Statement Addendum requested {requested_date.isoformat()} "
            f"not furnished within the {deadline_days}-day deadline "
            f"({deadline_date.isoformat()})"
        ),
    )


ELECTION_DATE_RESOLUTION_STATUSES = ("RESOLVED", "COMPLIANCE_REVIEW_REQUIRED")

# Risk 1 (election_date < signing date) / Risk 2 (missing election_date)
# validation reasons -- see ElectionDateResolution.validation_reason.
VALIDATION_REASON_MISSING_ELECTION_DATE = "MISSING_ELECTION_DATE"
VALIDATION_REASON_ELECTION_DATE_EARLIER_THAN_SIGNATURE = "ELECTION_DATE_EARLIER_THAN_SIGNATURE"


@dataclass(frozen=True)
class ElectionDateResolution:
    """
    Discriminated result of resolving the FY2027 election-addendum deadline
    source for an admission. RESOLVED means election_effective_date/
    benefit_period_id are safe to use to create/finalize an addendum
    deadline. COMPLIANCE_REVIEW_REQUIRED means a real data-quality problem
    was detected (Risk 1/Risk 2) -- the caller MUST NOT create or finalize
    an addendum deadline and must instead raise/track a compliance review
    record, per workflow-owner instruction ("Do not automatically replace
    the effective date with the signature date").
    """

    status: str
    admission_id: "uuid.UUID"
    patient_id: "uuid.UUID"
    benefit_period_id: "uuid.UUID | None"
    election_effective_date: "date | None"
    election_signed_at: "object | None"
    validation_reason: "str | None"


def resolve_election_effective_date_for_admission(db, admission_id) -> ElectionDateResolution:
    """
    Resolves the FY2027 mandatory-addendum election start date strictly
    from benefit_periods.election_date for the patient's INITIAL benefit
    period (benefit_type='INITIAL', period_number=1) -- this is the only
    authorized source (workflow-owner decision). admissions.election_signed_at
    is NEVER used, and there is NO silent fallback between the two.

    benefit periods is a genuine data-integrity error (Risk 3 assumes
    exactly one INITIAL/period_number=1 period per patient) and still
    raises ElectionAddendumComplianceError; it is not an expected
    operational state like Risk 1/Risk 2.
    """
    from app.models.admission import Admission
    from app.models.benefit_period import BenefitPeriod

    admission = db.get(Admission, admission_id)
    if admission is None:
        raise ElectionAddendumComplianceError(f"Admission {admission_id} not found")

    candidates = (
        db.query(BenefitPeriod)
        .filter(
            BenefitPeriod.patient_id == admission.patient_id,
            BenefitPeriod.benefit_type == "INITIAL",
            BenefitPeriod.period_number == 1,
        )
        .all()
    )

    if len(candidates) > 1:
        raise ElectionAddendumComplianceError(
            f"Ambiguous election source: {len(candidates)} INITIAL/period_number=1 "
            f"benefit_periods found for patient {admission.patient_id}; refusing to "
            f"guess which one applies to admission {admission_id}."
        )

    election_signed_at = admission.election_signed_at

    # Risk 2: no benefit_period, or one exists but election_date is NULL.
    # Addendum obligation stays REQUIRED but the deadline is UNRESOLVED --
    # never fall back to admissions.election_signed_at.
    if len(candidates) == 0 or candidates[0].election_date is None:
        benefit_period = candidates[0] if candidates else None
        return ElectionDateResolution(
            status="COMPLIANCE_REVIEW_REQUIRED",
            admission_id=admission_id,
            patient_id=admission.patient_id,
            benefit_period_id=benefit_period.id if benefit_period else None,
            election_effective_date=None,
            election_signed_at=election_signed_at,
            validation_reason=VALIDATION_REASON_MISSING_ELECTION_DATE,
        )

    benefit_period = candidates[0]

    # Risk 1: election_date earlier than the signature date is an invalid
    # condition (effective date may equal or follow the signing date, never
    # precede it). Flag for compliance review; do not create/finalize the
    # deadline and do not auto-correct.
    if election_signed_at is not None and benefit_period.election_date < election_signed_at.date():
        return ElectionDateResolution(
            status="COMPLIANCE_REVIEW_REQUIRED",
            admission_id=admission_id,
            patient_id=admission.patient_id,
            benefit_period_id=benefit_period.id,
            election_effective_date=benefit_period.election_date,
            election_signed_at=election_signed_at,
            validation_reason=VALIDATION_REASON_ELECTION_DATE_EARLIER_THAN_SIGNATURE,
        )

    return ElectionDateResolution(
        status="RESOLVED",
        admission_id=admission_id,
        patient_id=admission.patient_id,
        benefit_period_id=benefit_period.id,
        election_effective_date=benefit_period.election_date,
        election_signed_at=election_signed_at,
        validation_reason=None,
    )


def mandatory_rule_applies(election_effective_date: date) -> bool:
    """
    Whether the CMS FY2027 mandatory-for-every-election addendum rule
    applies to a hospice election with this election_effective_date.
    Callers must pass the verified persisted election start date --
    benefit_periods.election_date for the patient's INITIAL benefit
    period, NOT admissions.election_signed_at (a separate signature-
    completion timestamp).
    """
    if election_effective_date is None:
        raise ElectionAddendumComplianceError("election_effective_date is required")
    return election_effective_date >= MANDATORY_ADDENDUM_RULE_EFFECTIVE_DATE


@dataclass(frozen=True)
class MandatoryAddendumRequirement:
    trigger_type: str
    triggered_at_date: date
    required_by_date: date


def compute_mandatory_addendum_requirement(
    *,
    election_effective_date: date,
    poc_change_date: date | None = None,
) -> MandatoryAddendumRequirement:
    """
    CMS FY2027 mandatory-election addendum rule (elections on/after
    MANDATORY_ADDENDUM_RULE_EFFECTIVE_DATE):

      - Initial requirement: furnish within 5 days of the election start
        date (election_effective_date), regardless of any beneficiary
        request.
      - Plan-of-Care-change requirement: furnish an updated addendum
        within 3 days of the triggering Plan-of-Care determination
        change (poc_change_date), when provided.

    This function only computes the deadline from real, already-known
    dates -- it does not create or mutate any ElectionAddendumRequest row;
    callers are responsible for persisting the resulting requirement.
    """
    if not mandatory_rule_applies(election_effective_date):
        raise ElectionAddendumComplianceError(
            f"Mandatory addendum rule does not apply to elections before "
            f"{MANDATORY_ADDENDUM_RULE_EFFECTIVE_DATE.isoformat()}"
        )

    if poc_change_date is not None:
        return MandatoryAddendumRequirement(
            trigger_type="PLAN_OF_CARE_CHANGE",
            triggered_at_date=poc_change_date,
            required_by_date=poc_change_date + timedelta(days=MANDATORY_POC_CHANGE_UPDATE_DEADLINE_DAYS),
        )

    return MandatoryAddendumRequirement(
        trigger_type="MANDATORY_INITIAL_ELECTION",
        triggered_at_date=election_effective_date,
        required_by_date=election_effective_date + timedelta(days=MANDATORY_INITIAL_FURNISH_DEADLINE_DAYS),
    )


@dataclass(frozen=True)
class MandatoryAddendumOutcome:
    outcome: str  # NOT_APPLICABLE / COMPLIANCE_REVIEW_REQUIRED / CREATED / EXISTING
    election_addendum_request: "object | None"
    compliance_obligation: "object | None"


def _emit_compliance_audit_event(
    db,
    *,
    tenant_id,
    compliance_obligation_id,
    patient_id,
    admission_id,
    event_type,
    actor_user_id=None,
    actor_account_discipline=None,
    prior_value=None,
    new_value=None,
    reason=None,
):
    from app.models.compliance_obligation import ComplianceAuditEvent

    row = ComplianceAuditEvent(
        tenant_id=tenant_id,
        compliance_obligation_id=compliance_obligation_id,
        patient_id=patient_id,
        admission_id=admission_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        prior_value=prior_value,
        new_value=new_value,
        reason=reason,
    )
    db.add(row)
    db.flush()
    return row


def _emit_addendum_audit_event(
    db,
    *,
    tenant_id,
    addendum_request_id,
    patient_id,
    admission_id,
    event_type,
    actor_user_id=None,
    actor_account_discipline=None,
    prior_value=None,
    new_value=None,
    reason=None,
):
    from app.billing.models.election_addendum_request import ElectionAddendumAuditEvent

    row = ElectionAddendumAuditEvent(
        tenant_id=tenant_id,
        addendum_request_id=addendum_request_id,
        patient_id=patient_id,
        admission_id=admission_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        prior_value=prior_value,
        new_value=new_value,
        reason=reason,
    )
    db.add(row)
    db.flush()
    return row


def _get_or_create_mandatory_addendum_request_row(
    db,
    *,
    tenant_id,
    admission_id,
    patient_id,
    benefit_period_id,
    election_effective_date: date,
    created_by_user_id=None,
):
    """
    Shared idempotent creation of the MANDATORY_INITIAL_ELECTION
    ElectionAddendumRequest row. Used both by the normal RESOLVED path and
    by resolve_compliance_review() (which supplies a human-corrected
    election_effective_date after a compliance review).
    """
    from app.billing.models.election_addendum_request import ElectionAddendumRequest

    if not mandatory_rule_applies(election_effective_date):
        return MandatoryAddendumOutcome(outcome="NOT_APPLICABLE", election_addendum_request=None, compliance_obligation=None)

    existing = (
        db.query(ElectionAddendumRequest)
        .filter(
            ElectionAddendumRequest.tenant_id == tenant_id,
            ElectionAddendumRequest.admission_id == admission_id,
            ElectionAddendumRequest.trigger_type == "MANDATORY_INITIAL_ELECTION",
        )
        .first()
    )
    if existing is not None:
        return MandatoryAddendumOutcome(outcome="EXISTING", election_addendum_request=existing, compliance_obligation=None)

    requirement = compute_mandatory_addendum_requirement(election_effective_date=election_effective_date)

    row = ElectionAddendumRequest(
        tenant_id=tenant_id,
        patient_id=patient_id,
        admission_id=admission_id,
        benefit_period_id=benefit_period_id,
        trigger_type=requirement.trigger_type,
        triggered_at=None,
        election_effective_date=election_effective_date,
        required_by_at=datetime.combine(requirement.required_by_date, datetime.min.time(), tzinfo=timezone.utc),
        mandatory_rule_applies=True,
        created_by=str(created_by_user_id) if created_by_user_id else None,
    )
    db.add(row)
    db.flush()

    _emit_addendum_audit_event(
        db,
        tenant_id=tenant_id,
        addendum_request_id=row.id,
        patient_id=patient_id,
        admission_id=admission_id,
        event_type="REQUIREMENT_CREATED",
        actor_user_id=created_by_user_id,
        new_value={
            "trigger_type": requirement.trigger_type,
            "election_effective_date": election_effective_date.isoformat(),
            "required_by_date": requirement.required_by_date.isoformat(),
        },
    )
    return MandatoryAddendumOutcome(outcome="CREATED", election_addendum_request=row, compliance_obligation=None)


def get_or_create_mandatory_initial_addendum_requirement(
    db,
    *,
    tenant_id,
    admission_id,
    created_by_user_id=None,
):
    """
    Idempotently creates the MANDATORY_INITIAL_ELECTION ElectionAddendumRequest
    row for an admission whose election_effective_date (resolved strictly via
    resolve_election_effective_date_for_admission -- benefit_periods.election_date
    only, no fallback) is on/after MANDATORY_ADDENDUM_RULE_EFFECTIVE_DATE.

    Returns a MandatoryAddendumOutcome:
      - outcome="NOT_APPLICABLE": election_effective_date resolved cleanly
        but predates the mandatory rule; no row created; not an error.
      - outcome="COMPLIANCE_REVIEW_REQUIRED": Risk 1 (election_date earlier
        than election_signed_at) or Risk 2 (missing election_date) was
        detected. NO ElectionAddendumRequest deadline is created or
        finalized -- instead an OPEN compliance_obligations review record
        is created (or an existing open one for this admission is reused,
        idempotently) so the condition remains visible until a human
        corrects it. This function never guesses a substitute date. Use
        resolve_compliance_review() to resolve it once a human has
        confirmed the correct election date.
      - outcome="CREATED" / "EXISTING": the MANDATORY_INITIAL_ELECTION row,
        existing rows are returned unchanged and never re-dated.
    """
    from app.models.compliance_obligation import ComplianceObligation
    from app.models.admission import Admission

    admission = db.get(Admission, admission_id)
    if admission is None:
        raise ElectionAddendumComplianceError(f"Admission {admission_id} not found")

    resolved = resolve_election_effective_date_for_admission(db, admission_id)

    if resolved.status == "COMPLIANCE_REVIEW_REQUIRED":
        existing_obligation = (
            db.query(ComplianceObligation)
            .filter(
                ComplianceObligation.tenant_id == tenant_id,
                ComplianceObligation.admission_id == admission_id,
                ComplianceObligation.obligation_type == "ELECTION_ADDENDUM_DATE_VALIDATION_REVIEW",
                ComplianceObligation.status == "OPEN",
            )
            .first()
        )
        if existing_obligation is not None:
            return MandatoryAddendumOutcome(
                outcome="COMPLIANCE_REVIEW_REQUIRED",
                election_addendum_request=None,
                compliance_obligation=existing_obligation,
            )

        now = datetime.now(timezone.utc)
        obligation = ComplianceObligation(
            tenant_id=tenant_id,
            patient_id=admission.patient_id,
            admission_id=admission_id,
            benefit_period_id=resolved.benefit_period_id,
            obligation_type="ELECTION_ADDENDUM_DATE_VALIDATION_REVIEW",
            regulatory_basis="CMS-1851-F / FY2027 Hospice Final Rule",
            status="OPEN",
            required_by_at=now,
            source_record_type="ADMISSION",
            source_record_id=admission_id,
            notes=(
                f"validation_reason={resolved.validation_reason}; "
                f"benefit_period_id={resolved.benefit_period_id}; "
                f"election_date={resolved.election_effective_date}; "
                f"election_signed_at={resolved.election_signed_at}; "
                f"detected_at={now.isoformat()}"
            ),
            created_by=created_by_user_id,
        )
        db.add(obligation)
        db.flush()

        _emit_compliance_audit_event(
            db,
            tenant_id=tenant_id,
            compliance_obligation_id=obligation.id,
            patient_id=admission.patient_id,
            admission_id=admission_id,
            event_type="REQUIREMENT_CREATED",
            actor_user_id=created_by_user_id,
            new_value={
                "obligation_type": "ELECTION_ADDENDUM_DATE_VALIDATION_REVIEW",
                "validation_reason": resolved.validation_reason,
            },
        )
        return MandatoryAddendumOutcome(
            outcome="COMPLIANCE_REVIEW_REQUIRED",
            election_addendum_request=None,
            compliance_obligation=obligation,
        )

    if not mandatory_rule_applies(resolved.election_effective_date):
        return MandatoryAddendumOutcome(
            outcome="NOT_APPLICABLE", election_addendum_request=None, compliance_obligation=None
        )

    return _get_or_create_mandatory_addendum_request_row(
        db,
        tenant_id=tenant_id,
        admission_id=admission_id,
        patient_id=admission.patient_id,
        benefit_period_id=resolved.benefit_period_id,
        election_effective_date=resolved.election_effective_date,
        created_by_user_id=created_by_user_id,
    )


COMPLIANCE_REVIEW_OBLIGATION_TYPE = "ELECTION_ADDENDUM_DATE_VALIDATION_REVIEW"


def resolve_compliance_review(
    db,
    *,
    tenant_id,
    compliance_obligation_id,
    benefit_period_id,
    resolved_election_date: date,
    resolution_reason: str,
    resolved_by_user_id,
    actor_account_discipline=None,
) -> MandatoryAddendumOutcome:
    """
    Resolves an open ELECTION_ADDENDUM_DATE_VALIDATION_REVIEW compliance
    obligation with a human-confirmed election date, then idempotently
    creates the mandatory-addendum requirement from that resolved date.

    Original benefit_period/admission data is never overwritten -- the
    resolved_election_date is only used to compute the deadline and to
    populate the new ElectionAddendumRequest row. Resolution and
    requirement creation happen in one atomic step: if requirement
    creation fails, the obligation resolution is rolled back too.
    """
    from app.models.compliance_obligation import ComplianceObligation
    from app.models.admission import Admission
    from app.models.benefit_period import BenefitPeriod
    from app.models.record_version import RecordVersion

    if not resolution_reason:
        raise ElectionAddendumComplianceError("resolution_reason is required")
    if resolved_election_date is None:
        raise ElectionAddendumComplianceError("resolved_election_date is required")

    # tenant_id is normalized to str() -- see clinical_outcome_service.get_outcome_record
    # for why raw UUID-vs-str equality here would silently produce a false not-found.
    obligation = db.get(ComplianceObligation, compliance_obligation_id)
    if obligation is None or str(obligation.tenant_id) != str(tenant_id):
        raise ElectionAddendumComplianceError(f"Compliance obligation {compliance_obligation_id} not found")
    if obligation.obligation_type != COMPLIANCE_REVIEW_OBLIGATION_TYPE:
        raise ElectionAddendumComplianceError("Obligation is not an election-addendum date validation review")
    if obligation.status != "OPEN":
        raise ElectionAddendumComplianceError(
            f"Compliance review {compliance_obligation_id} is not OPEN (status={obligation.status}); "
            "it may already be resolved."
        )

    benefit_period = db.get(BenefitPeriod, benefit_period_id)
    if benefit_period is None or benefit_period.patient_id != obligation.patient_id:
        raise ElectionAddendumComplianceError(
            "benefit_period does not belong to the same patient as the compliance review"
        )

    admission = db.get(Admission, obligation.admission_id) if obligation.admission_id else None
    if admission is None or admission.patient_id != benefit_period.patient_id:
        raise ElectionAddendumComplianceError(
            "benefit_period does not belong to the same admission as the compliance review"
        )

    if admission.election_signed_at is not None and resolved_election_date < admission.election_signed_at.date():
        raise ElectionAddendumComplianceError(
            "resolved_election_date cannot be earlier than the election signature date"
        )

    # Preserve the original obligation state before mutating it.
    prior_state = {
        "status": obligation.status,
        "required_by_at": obligation.required_by_at.isoformat() if obligation.required_by_at else None,
        "notes": obligation.notes,
    }

    existing_version_count = (
        db.query(RecordVersion)
        .filter(
            RecordVersion.tenant_id == tenant_id,
            RecordVersion.source_record_type == "COMPLIANCE_OBLIGATION",
            RecordVersion.source_record_id == obligation.id,
        )
        .count()
    )
    db.add(
        RecordVersion(
            tenant_id=tenant_id,
            source_record_type="COMPLIANCE_OBLIGATION",
            source_record_id=obligation.id,
            version_number=existing_version_count + 1,
            snapshot=prior_state,
            change_reason=resolution_reason,
            created_by=resolved_by_user_id,
        )
    )

    try:
        now = datetime.now(timezone.utc)
        obligation.status = "COMPLETED"
        obligation.completed_at = now
        obligation.completion_evidence_reference = f"resolved_election_date={resolved_election_date.isoformat()}"
        obligation.notes = (obligation.notes or "") + (
            f" | RESOLVED at {now.isoformat()} by {resolved_by_user_id}: "
            f"resolved_election_date={resolved_election_date.isoformat()}; reason={resolution_reason}"
        )
        db.flush()

        _emit_compliance_audit_event(
            db,
            tenant_id=tenant_id,
            compliance_obligation_id=obligation.id,
            patient_id=obligation.patient_id,
            admission_id=obligation.admission_id,
            event_type="RECORD_FINALIZED",
            actor_user_id=resolved_by_user_id,
            actor_account_discipline=actor_account_discipline,
            prior_value=prior_state,
            new_value={"status": "COMPLETED", "resolved_election_date": resolved_election_date.isoformat()},
            reason=resolution_reason,
        )

        outcome = _get_or_create_mandatory_addendum_request_row(
            db,
            tenant_id=tenant_id,
            admission_id=obligation.admission_id,
            patient_id=obligation.patient_id,
            benefit_period_id=benefit_period_id,
            election_effective_date=resolved_election_date,
            created_by_user_id=resolved_by_user_id,
        )
    except Exception:
        db.rollback()
        raise

    return outcome


def reopen_compliance_review(
    db,
    *,
    tenant_id,
    compliance_obligation_id,
    reopen_reason: str,
    reopened_by_user_id,
    actor_account_discipline=None,
):
    """
    Reopens a previously resolved (COMPLETED) compliance review. Never
    touches any ElectionAddendumRequest row that may already have been
    created/furnished/finalized as a result of the earlier resolution --
    reopening only reopens the review itself for re-review.
    """
    from app.models.compliance_obligation import ComplianceObligation
    from app.models.record_version import RecordVersion

    if not reopen_reason:
        raise ElectionAddendumComplianceError("reopen_reason is required")
    if not reopened_by_user_id:
        raise ElectionAddendumComplianceError("reopened_by_user_id (authorized actor) is required")

    # tenant_id is normalized to str() -- see clinical_outcome_service.get_outcome_record
    # for why raw UUID-vs-str equality here would silently produce a false not-found.
    obligation = db.get(ComplianceObligation, compliance_obligation_id)
    if obligation is None or str(obligation.tenant_id) != str(tenant_id):
        raise ElectionAddendumComplianceError(f"Compliance obligation {compliance_obligation_id} not found")
    if obligation.status != "COMPLETED":
        raise ElectionAddendumComplianceError("Only a resolved (COMPLETED) compliance review may be reopened")

    prior_state = {
        "status": obligation.status,
        "completed_at": obligation.completed_at.isoformat() if obligation.completed_at else None,
        "completion_evidence_reference": obligation.completion_evidence_reference,
        "notes": obligation.notes,
    }
    existing_version_count = (
        db.query(RecordVersion)
        .filter(
            RecordVersion.tenant_id == tenant_id,
            RecordVersion.source_record_type == "COMPLIANCE_OBLIGATION",
            RecordVersion.source_record_id == obligation.id,
        )
        .count()
    )
    db.add(
        RecordVersion(
            tenant_id=tenant_id,
            source_record_type="COMPLIANCE_OBLIGATION",
            source_record_id=obligation.id,
            version_number=existing_version_count + 1,
            snapshot=prior_state,
            change_reason=reopen_reason,
            created_by=reopened_by_user_id,
        )
    )

    now = datetime.now(timezone.utc)
    obligation.status = "OPEN"
    obligation.completed_at = None
    obligation.notes = (obligation.notes or "") + (
        f" | REOPENED at {now.isoformat()} by {reopened_by_user_id}: reason={reopen_reason}"
    )
    db.flush()

    _emit_compliance_audit_event(
        db,
        tenant_id=tenant_id,
        compliance_obligation_id=obligation.id,
        patient_id=obligation.patient_id,
        admission_id=obligation.admission_id,
        event_type="RECORD_REOPENED",
        actor_user_id=reopened_by_user_id,
        actor_account_discipline=actor_account_discipline,
        prior_value=prior_state,
        new_value={"status": "OPEN"},
        reason=reopen_reason,
    )
    return obligation


# =====================================================================
# Relatedness-review-centered addendum workflow (FY2027 unusual case)
#
# Workflow-owner decision: the operational risk is DELAYED RELATEDNESS
# DETERMINATION (e.g. dialysis, specialty medications, transplant-related
# therapies, unusual DME, complex coverage determinations requiring
# physician review) -- not document finalization. State machine:
#
#   REQUIREMENT_CREATED -> PENDING_RELATEDNESS_REVIEW -> READY_FOR_GENERATION
#     -> ADDENDUM_GENERATED -> ADDENDUM_FURNISHED
#   (EXCEPTION_CLOSED reachable from any open state)
#
# PENDING_RELATEDNESS_REVIEW / physician review / generation NEVER stop or
# satisfy the 5-day/3-day compliance clock (required_by_at) -- only actual
# furnishing evidence or a documented regulatory exception closes it.
#
# The system supports item-level relatedness/coverage determination
# (election_addendum_determinations, reused -- not a second table); it
# never infers relatedness or coverage from diagnosis, supply type,
# medication class, payer, or current supplier. A human actor must record
# each item's determination explicitly.
# =====================================================================


def start_relatedness_review(
    db,
    *,
    addendum_request,
    reason: str,
    actor_user_id,
    actor_account_discipline: str | None = None,
) -> "object":
    """
    Marks an unusual case as requiring item-level relatedness review.
    Transitions REQUIREMENT_CREATED -> PENDING_RELATEDNESS_REVIEW. Does
    NOT stop or extend required_by_at.
    """
    if addendum_request.workflow_status != "REQUIREMENT_CREATED":
        raise ElectionAddendumComplianceError(
            f"Cannot start relatedness review from status {addendum_request.workflow_status!r}; "
            "expected REQUIREMENT_CREATED."
        )
    if not reason:
        raise ElectionAddendumComplianceError("reason is required to start a relatedness review")
    if not actor_user_id:
        raise ElectionAddendumComplianceError("An authorized actor is required to start a relatedness review")

    now = datetime.now(timezone.utc)
    addendum_request.relatedness_review_started_at = now
    addendum_request.relatedness_review_started_by_user_id = actor_user_id
    addendum_request.relatedness_review_reason = reason
    addendum_request.workflow_status = "PENDING_RELATEDNESS_REVIEW"
    db.flush()

    _emit_addendum_audit_event(
        db,
        tenant_id=addendum_request.tenant_id,
        addendum_request_id=addendum_request.id,
        patient_id=addendum_request.patient_id,
        admission_id=addendum_request.admission_id,
        event_type="RELATEDNESS_REVIEW_STARTED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        reason=reason,
        new_value={"workflow_status": "PENDING_RELATEDNESS_REVIEW"},
    )
    return addendum_request


def add_relatedness_item(
    db,
    *,
    addendum_request,
    determination_type: str,
    description: str,
    effective_date: date,
    current_provider_or_supplier: str | None = None,
    source_record_type: str | None = None,
    source_record_id=None,
    actor_user_id,
    actor_account_discipline: str | None = None,
) -> "object":
    """
    Adds one disputed condition/item/service/drug/supply/DME/dialysis
    component for relatedness review. Starts PENDING_REVIEW -- the
    system never infers RELATED/UNRELATED or coverage_owner at creation
    time; a human actor must record the determination explicitly via
    record_relatedness_item_determination().
    """
    from app.billing.models.election_addendum_request import ElectionAddendumDetermination

    if addendum_request.workflow_status != "PENDING_RELATEDNESS_REVIEW":
        raise ElectionAddendumComplianceError(
            f"Cannot add a relatedness item while workflow_status is {addendum_request.workflow_status!r}; "
            "expected PENDING_RELATEDNESS_REVIEW (call start_relatedness_review first)."
        )
    if not description:
        raise ElectionAddendumComplianceError("description is required")

    item = ElectionAddendumDetermination(
        tenant_id=addendum_request.tenant_id,
        addendum_request_id=addendum_request.id,
        determination_type=determination_type,
        description=description,
        relationship_status="PENDING_REVIEW",
        coverage_status=None,
        effective_date=effective_date,
        current_provider_or_supplier=current_provider_or_supplier,
        source_record_type=source_record_type,
        source_record_id=source_record_id,
        created_by=actor_user_id,
    )
    db.add(item)
    db.flush()

    _emit_addendum_audit_event(
        db,
        tenant_id=addendum_request.tenant_id,
        addendum_request_id=addendum_request.id,
        patient_id=addendum_request.patient_id,
        admission_id=addendum_request.admission_id,
        event_type="RELATEDNESS_ITEM_CREATED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        new_value={
            "determination_id": str(item.id),
            "determination_type": determination_type,
            "description": description,
        },
    )
    return item


def record_relatedness_item_determination(
    db,
    *,
    addendum_request,
    item,
    relationship_status: str,
    coverage_status: str,
    coverage_owner: str,
    clinical_rationale: str | None = None,
    actor_user_id,
    actor_account_discipline: str | None = None,
) -> "object":
    """
    Records the human clinical determination for one relatedness item.
    The system supports the determination; it does not make it -- this
    call always requires an explicit relationship_status/coverage_status/
    coverage_owner from the caller, never derived from diagnosis, supply
    type, medication class, payer, or current supplier.
    """
    if item.addendum_request_id != addendum_request.id:
        raise ElectionAddendumComplianceError("item does not belong to the given addendum_request")
    if relationship_status not in ("RELATED", "UNRELATED"):
        raise ElectionAddendumComplianceError("relationship_status must be RELATED or UNRELATED")
    if coverage_status not in ("COVERED", "NOT_COVERED"):
        raise ElectionAddendumComplianceError("coverage_status must be COVERED or NOT_COVERED")
    if not coverage_owner or coverage_owner == "UNDETERMINED":
        raise ElectionAddendumComplianceError("A determined coverage_owner is required (not UNDETERMINED)")
    if relationship_status == "UNRELATED" and not clinical_rationale:
        raise ElectionAddendumComplianceError("clinical_rationale is required when relationship_status is UNRELATED")
    if not actor_user_id:
        raise ElectionAddendumComplianceError("An authorized actor is required to record a determination")

    now = datetime.now(timezone.utc)
    item.relationship_status = relationship_status
    item.coverage_status = coverage_status
    item.coverage_owner = coverage_owner
    item.clinical_rationale = clinical_rationale
    item.reviewed_at = now
    item.reviewed_by_user_id = actor_user_id
    db.flush()

    _emit_addendum_audit_event(
        db,
        tenant_id=addendum_request.tenant_id,
        addendum_request_id=addendum_request.id,
        patient_id=addendum_request.patient_id,
        admission_id=addendum_request.admission_id,
        event_type="RELATEDNESS_ITEM_DETERMINED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        new_value={
            "determination_id": str(item.id),
            "relationship_status": relationship_status,
            "coverage_status": coverage_status,
            "coverage_owner": coverage_owner,
        },
    )
    return item


def request_physician_review(
    db,
    *,
    addendum_request,
    physician_user_id,
    actor_user_id,
    actor_account_discipline: str | None = None,
) -> "object":
    """
    Flags that physician review is required before the relatedness review
    can be completed. Keeps the 5-day clock active; does not stop it.
    """
    if addendum_request.workflow_status != "PENDING_RELATEDNESS_REVIEW":
        raise ElectionAddendumComplianceError(
            f"Cannot request physician review from status {addendum_request.workflow_status!r}; "
            "expected PENDING_RELATEDNESS_REVIEW."
        )
    if not physician_user_id:
        raise ElectionAddendumComplianceError("physician_user_id is required")

    addendum_request.physician_review_required = True
    addendum_request.physician_review_requested_at = datetime.now(timezone.utc)
    addendum_request.physician_reviewer_user_id = physician_user_id
    db.flush()

    _emit_addendum_audit_event(
        db,
        tenant_id=addendum_request.tenant_id,
        addendum_request_id=addendum_request.id,
        patient_id=addendum_request.patient_id,
        admission_id=addendum_request.admission_id,
        event_type="PHYSICIAN_REVIEW_REQUESTED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        new_value={"physician_reviewer_user_id": str(physician_user_id)},
    )
    return addendum_request


def complete_physician_review(
    db,
    *,
    addendum_request,
    rationale: str,
    actor_user_id,
    actor_account_discipline: str | None = None,
) -> "object":
    """
    Records physician review completion. Blocked until every relatedness
    item for this request has left PENDING_REVIEW -- physician review
    completion cannot itself substitute for the required per-item
    determinations.
    """
    from app.billing.models.election_addendum_request import ElectionAddendumDetermination

    if addendum_request.workflow_status != "PENDING_RELATEDNESS_REVIEW":
        raise ElectionAddendumComplianceError(
            f"Cannot complete physician review from status {addendum_request.workflow_status!r}; "
            "expected PENDING_RELATEDNESS_REVIEW."
        )
    if not addendum_request.physician_review_required or not addendum_request.physician_reviewer_user_id:
        raise ElectionAddendumComplianceError("Physician review was not requested for this addendum requirement")
    pending_items = (
        db.query(ElectionAddendumDetermination)
        .filter(
            ElectionAddendumDetermination.addendum_request_id == addendum_request.id,
            ElectionAddendumDetermination.relationship_status == "PENDING_REVIEW",
        )
        .count()
    )
    if pending_items:
        raise ElectionAddendumComplianceError(
            f"Cannot complete physician review while {pending_items} relatedness item(s) remain PENDING_REVIEW"
        )
    if not rationale:
        raise ElectionAddendumComplianceError("rationale is required to complete physician review")

    addendum_request.physician_reviewed_at = datetime.now(timezone.utc)
    addendum_request.physician_review_rationale = rationale
    db.flush()

    _emit_addendum_audit_event(
        db,
        tenant_id=addendum_request.tenant_id,
        addendum_request_id=addendum_request.id,
        patient_id=addendum_request.patient_id,
        admission_id=addendum_request.admission_id,
        event_type="PHYSICIAN_REVIEW_COMPLETED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        reason=rationale,
    )
    return addendum_request


def complete_relatedness_review(
    db,
    *,
    addendum_request,
    clinical_rationale: str,
    actor_user_id,
    actor_account_discipline: str | None = None,
) -> "object":
    """
    Completes the relatedness review and transitions
    PENDING_RELATEDNESS_REVIEW -> READY_FOR_GENERATION. Blocked unless:
      - no relatedness item remains PENDING_REVIEW
      - no relatedness item has coverage_owner UNDETERMINED
      - physician review is complete, if it was required
      - an overall clinical_rationale is supplied
    """
    from app.billing.models.election_addendum_request import ElectionAddendumDetermination

    if addendum_request.workflow_status != "PENDING_RELATEDNESS_REVIEW":
        raise ElectionAddendumComplianceError(
            f"Cannot complete relatedness review from status {addendum_request.workflow_status!r}; "
            "expected PENDING_RELATEDNESS_REVIEW."
        )
    items = (
        db.query(ElectionAddendumDetermination)
        .filter(ElectionAddendumDetermination.addendum_request_id == addendum_request.id)
        .all()
    )
    if not items:
        raise ElectionAddendumComplianceError(
            "At least one relatedness item is required before completing the review."
        )
    pending = [i for i in items if i.relationship_status == "PENDING_REVIEW"]
    if pending:
        raise ElectionAddendumComplianceError(
            f"Cannot complete relatedness review while {len(pending)} item(s) remain PENDING_REVIEW"
        )
    undetermined_owner = [i for i in items if not i.coverage_owner or i.coverage_owner == "UNDETERMINED"]
    if undetermined_owner:
        raise ElectionAddendumComplianceError(
            f"Cannot complete relatedness review while {len(undetermined_owner)} item(s) have an UNDETERMINED coverage_owner"
        )
    if addendum_request.physician_review_required and not addendum_request.physician_reviewed_at:
        raise ElectionAddendumComplianceError(
            "Physician review was required for this addendum requirement and has not been completed"
        )
    if not clinical_rationale:
        raise ElectionAddendumComplianceError("clinical_rationale is required to complete the relatedness review")
    if not actor_user_id:
        raise ElectionAddendumComplianceError("An authorized actor is required to complete the relatedness review")

    now = datetime.now(timezone.utc)
    addendum_request.relatedness_determined_at = now
    addendum_request.relatedness_determined_by_user_id = actor_user_id
    addendum_request.clinical_rationale = clinical_rationale
    addendum_request.workflow_status = "READY_FOR_GENERATION"
    db.flush()

    _emit_addendum_audit_event(
        db,
        tenant_id=addendum_request.tenant_id,
        addendum_request_id=addendum_request.id,
        patient_id=addendum_request.patient_id,
        admission_id=addendum_request.admission_id,
        event_type="RELATEDNESS_DETERMINED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        reason=clinical_rationale,
        new_value={"workflow_status": "READY_FOR_GENERATION", "relatedness_determined_at": now.isoformat()},
    )
    return addendum_request


def generate_addendum_document(
    db,
    *,
    addendum_request,
    document_reference: str,
    document_version: int,
    actor_user_id,
    actor_account_discipline: str | None = None,
) -> "object":
    """
    Records that the patient-specific addendum document has been
    generated. Requires READY_FOR_GENERATION -- a document cannot be
    generated while relatedness review is still pending. Generation does
    NOT stop or satisfy the compliance clock; only furnishing does.
    """
    if addendum_request.workflow_status != "READY_FOR_GENERATION":
        raise ElectionAddendumComplianceError(
            f"Cannot generate addendum document from status {addendum_request.workflow_status!r}; "
            "expected READY_FOR_GENERATION."
        )
    if not document_reference:
        raise ElectionAddendumComplianceError("document_reference is required to generate the addendum")
    if not document_version or document_version <= 0:
        raise ElectionAddendumComplianceError("document_version must be a positive integer")

    addendum_request.document_reference = document_reference
    addendum_request.document_version = document_version
    addendum_request.generated_at = datetime.now(timezone.utc)
    addendum_request.workflow_status = "ADDENDUM_GENERATED"
    db.flush()

    _emit_addendum_audit_event(
        db,
        tenant_id=addendum_request.tenant_id,
        addendum_request_id=addendum_request.id,
        patient_id=addendum_request.patient_id,
        admission_id=addendum_request.admission_id,
        event_type="ADDENDUM_GENERATED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        new_value={
            "workflow_status": "ADDENDUM_GENERATED",
            "document_reference": document_reference,
            "document_version": document_version,
        },
    )
    return addendum_request


def record_furnishing(
    db,
    *,
    addendum_request,
    furnished_at: datetime,
    furnished_to: str,
    furnishing_method: str,
    bfcc_qio_information_furnished: bool,
    actor_user_id,
    actor_account_discipline: str | None = None,
) -> "object":
    """
    Records evidence that the patient/representative actually received
    the generated document. This is the ONLY event (besides a documented
    exception) that closes the compliance requirement -- requires
    ADDENDUM_GENERATED, and furnished_at must be on/after generated_at.
    """
    if addendum_request.workflow_status != "ADDENDUM_GENERATED":
        raise ElectionAddendumComplianceError(
            f"Cannot record furnishing from status {addendum_request.workflow_status!r}; expected ADDENDUM_GENERATED."
        )
    if furnished_to not in ("PATIENT", "REPRESENTATIVE"):
        raise ElectionAddendumComplianceError("furnished_to must be PATIENT or REPRESENTATIVE")
    if not furnishing_method:
        raise ElectionAddendumComplianceError("furnishing_method is required")
    if addendum_request.generated_at and furnished_at < addendum_request.generated_at:
        raise ElectionAddendumComplianceError("furnished_at cannot be before generated_at")
    if not bfcc_qio_information_furnished:
        raise ElectionAddendumComplianceError("BFCC-QIO Immediate Advocacy information must be furnished")
    if not actor_user_id:
        raise ElectionAddendumComplianceError("An authorized actor is required to record furnishing")

    addendum_request.furnished_at = furnished_at
    addendum_request.furnished_by_user_id = actor_user_id
    addendum_request.furnished_to = furnished_to
    addendum_request.furnishing_method = furnishing_method
    addendum_request.bfcc_qio_information_furnished = True
    addendum_request.workflow_status = "ADDENDUM_FURNISHED"
    db.flush()

    _emit_addendum_audit_event(
        db,
        tenant_id=addendum_request.tenant_id,
        addendum_request_id=addendum_request.id,
        patient_id=addendum_request.patient_id,
        admission_id=addendum_request.admission_id,
        event_type="ADDENDUM_FURNISHED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        new_value={
            "workflow_status": "ADDENDUM_FURNISHED",
            "furnished_at": furnished_at.isoformat(),
            "furnished_to": furnished_to,
            "furnishing_method": furnishing_method,
        },
    )
    return addendum_request


def record_acknowledgment(
    db,
    *,
    addendum_request,
    acknowledgment_status: str,
    acknowledgment_document_reference: str | None = None,
    signature_exception_reason: str | None = None,
    actor_user_id,
    actor_account_discipline: str | None = None,
) -> "object":
    """
    Records the packet-level signature outcome for this addendum version
    (Love & Faith uses a packet acknowledgment model; this does not
    create a separate standalone signature workflow). furnished_at
    (receipt) and acknowledgment_at (signature) remain separate events.
    """
    valid_statuses = (
        "PENDING",
        "SIGNED_BY_PATIENT",
        "SIGNED_BY_REPRESENTATIVE",
        "REFUSED",
        "UNABLE_TO_SIGN",
        "NOT_REQUIRED_DUE_TO_EXCEPTION",
    )
    if acknowledgment_status not in valid_statuses:
        raise ElectionAddendumComplianceError(f"acknowledgment_status must be one of {valid_statuses}")
    if acknowledgment_status in ("REFUSED", "UNABLE_TO_SIGN") and not signature_exception_reason:
        raise ElectionAddendumComplianceError(
            "signature_exception_reason is required when acknowledgment_status is REFUSED or UNABLE_TO_SIGN"
        )
    if not actor_user_id:
        raise ElectionAddendumComplianceError("An authorized actor is required to record an acknowledgment")

    addendum_request.acknowledgment_status = acknowledgment_status
    addendum_request.acknowledgment_at = datetime.now(timezone.utc)
    addendum_request.acknowledgment_document_reference = acknowledgment_document_reference
    addendum_request.signature_exception_reason = signature_exception_reason
    db.flush()

    event_type = "ACKNOWLEDGMENT_REFUSED" if acknowledgment_status == "REFUSED" else "ACKNOWLEDGMENT_RECORDED"
    _emit_addendum_audit_event(
        db,
        tenant_id=addendum_request.tenant_id,
        addendum_request_id=addendum_request.id,
        patient_id=addendum_request.patient_id,
        admission_id=addendum_request.admission_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        reason=signature_exception_reason,
        new_value={
            "acknowledgment_status": acknowledgment_status,
            "acknowledgment_document_reference": acknowledgment_document_reference,
        },
    )
    return addendum_request


def record_exception(
    db,
    *,
    addendum_request,
    exception_type: str,
    exception_occurred_at: datetime,
    reason: str,
    actor_user_id,
    actor_account_discipline: str | None = None,
) -> "object":
    """
    Closes the requirement via a permitted regulatory exception (death,
    election revocation, or discharge before furnishing). Reachable from
    any open state; requires exception_type, exception_occurred_at, and a
    documented reason.
    """
    valid_types = ("PATIENT_DIED", "ELECTION_REVOKED", "PATIENT_DISCHARGED", "OTHER_ALLOWED_EXCEPTION")
    if addendum_request.workflow_status in ("ADDENDUM_FURNISHED", "EXCEPTION_CLOSED"):
        raise ElectionAddendumComplianceError(
            f"Cannot record an exception from status {addendum_request.workflow_status!r}; "
            "the requirement is already closed."
        )
    if exception_type not in valid_types:
        raise ElectionAddendumComplianceError(f"exception_type must be one of {valid_types}")
    if not exception_occurred_at:
        raise ElectionAddendumComplianceError("exception_occurred_at is required")
    if not reason:
        raise ElectionAddendumComplianceError("reason is required to record an exception")
    if not actor_user_id:
        raise ElectionAddendumComplianceError("An authorized actor is required to record an exception")

    addendum_request.exception_type = exception_type
    addendum_request.exception_occurred_at = exception_occurred_at
    addendum_request.workflow_status = "EXCEPTION_CLOSED"
    db.flush()

    _emit_addendum_audit_event(
        db,
        tenant_id=addendum_request.tenant_id,
        addendum_request_id=addendum_request.id,
        patient_id=addendum_request.patient_id,
        admission_id=addendum_request.admission_id,
        event_type="EXCEPTION_RECORDED",
        actor_user_id=actor_user_id,
        actor_account_discipline=actor_account_discipline,
        reason=reason,
        new_value={"workflow_status": "EXCEPTION_CLOSED", "exception_type": exception_type},
    )
    return addendum_request


def create_addendum_update_for_relatedness_change(
    db,
    *,
    prior_addendum_request,
    poc_change_date: date,
    created_by_user_id,
    actor_account_discipline: str | None = None,
) -> "object":
    """
    Update-tracking when a qualifying Plan-of-Care change affects the
    addendum determinations: creates a new, versioned
    ElectionAddendumRequest row (trigger_type=PLAN_OF_CARE_CHANGE,
    supersedes_request_id=prior_addendum_request.id) with its own 3-day
    PLAN_OF_CARE_CHANGE furnishing deadline and its own fresh
    REQUIREMENT_CREATED workflow_status -- the changed relatedness
    determination must go through review again before a new addendum can
    be generated/furnished. Never mutates the prior (possibly already-
    furnished) row's items in place, so the prior furnished version
    remains retrievable.
    """
    from app.billing.models.election_addendum_request import ElectionAddendumRequest

    requirement = compute_mandatory_addendum_requirement(
        election_effective_date=prior_addendum_request.election_effective_date,
        poc_change_date=poc_change_date,
    )

    new_row = ElectionAddendumRequest(
        tenant_id=prior_addendum_request.tenant_id,
        patient_id=prior_addendum_request.patient_id,
        admission_id=prior_addendum_request.admission_id,
        benefit_period_id=prior_addendum_request.benefit_period_id,
        trigger_type="PLAN_OF_CARE_CHANGE",
        triggered_at=datetime.combine(poc_change_date, datetime.min.time(), tzinfo=timezone.utc),
        election_effective_date=prior_addendum_request.election_effective_date,
        required_by_at=datetime.combine(requirement.required_by_date, datetime.min.time(), tzinfo=timezone.utc),
        mandatory_rule_applies=True,
        version_number=prior_addendum_request.version_number + 1,
        supersedes_request_id=prior_addendum_request.id,
        created_by=str(created_by_user_id) if created_by_user_id else None,
    )
    db.add(new_row)
    db.flush()

    _emit_addendum_audit_event(
        db,
        tenant_id=prior_addendum_request.tenant_id,
        addendum_request_id=new_row.id,
        patient_id=prior_addendum_request.patient_id,
        admission_id=prior_addendum_request.admission_id,
        event_type="ADDENDUM_UPDATE_REQUIRED",
        actor_user_id=created_by_user_id,
        actor_account_discipline=actor_account_discipline,
        reason="Relatedness determination changed following a Plan-of-Care update",
        new_value={
            "trigger_type": "PLAN_OF_CARE_CHANGE",
            "supersedes_request_id": str(prior_addendum_request.id),
            "required_by_date": requirement.required_by_date.isoformat(),
        },
    )
    _emit_addendum_audit_event(
        db,
        tenant_id=prior_addendum_request.tenant_id,
        addendum_request_id=prior_addendum_request.id,
        patient_id=prior_addendum_request.patient_id,
        admission_id=prior_addendum_request.admission_id,
        event_type="ADDENDUM_SUPERSEDED",
        actor_user_id=created_by_user_id,
        actor_account_discipline=actor_account_discipline,
        reason="Superseded by a new relatedness-change addendum requirement",
        new_value={"superseded_by_id": str(new_row.id)},
    )
    return new_row


