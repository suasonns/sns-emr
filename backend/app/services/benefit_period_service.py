# backend/app/services/benefit_period_service.py

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Literal, Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.benefit_period import BenefitPeriod
from app.models.benefit_period_status_event import BenefitPeriodStatusEvent
from app.models.enums import (
    TaskDiscipline,
    TaskOrigin,
    TaskRegulatoryBasis,
    TaskType,
)
from app.models.patient import Patient
from app.models.task import Task
from app.services.task_benefit_period_linker import (
    attach_active_benefit_period_to_task,
)

logger = logging.getLogger("sns_emr")

AllowedBenefitType = Literal["INITIAL", "RECERT"]


def _cms_benefit_period_length_days(period_number: int) -> int:
    """
    CMS hospice election periods:
    - BP1: 90 days
    - BP2: 90 days
    - BP3+: 60 days
    """
    if period_number in (1, 2):
        return 90
    return 60


def _snapshot_benefit_period(bp: Optional[BenefitPeriod]) -> Optional[dict[str, Any]]:
    """
    JSON-safe snapshot of a BenefitPeriod row for
    BenefitPeriodStatusEvent.previous_value / new_value (Eligibility
    Traceability Epic, Workstream 1). None in, None out -- used for
    previous_value on the very first (CREATED) event, where there is no
    prior row.
    """
    if bp is None:
        return None
    return {
        "id": str(bp.id),
        "benefit_type": bp.benefit_type,
        "period_number": bp.period_number,
        "election_date": bp.election_date.isoformat() if bp.election_date else None,
        "start_date": bp.start_date.isoformat() if bp.start_date else None,
        "end_date": bp.end_date.isoformat() if bp.end_date else None,
        "is_current": bp.is_current,
    }


def record_benefit_period_event(
    db: Session,
    *,
    tenant_id: UUID,
    benefit_period_id: UUID,
    event_type: str,
    actor_user_id: UUID,
    new_value: dict[str, Any],
    previous_value: Optional[dict[str, Any]] = None,
    reason: Optional[str] = None,
    related_certification_id: Optional[UUID] = None,
) -> BenefitPeriodStatusEvent:
    """
    Writes one immutable BenefitPeriodStatusEvent row (Eligibility
    Traceability Epic, Workstream 1). Never updated or deleted. Callers
    are responsible for wrapping this in the same transaction as the
    benefit-period state change it documents, so the two can never drift
    (see rollover_benefit_period below).
    """
    event = BenefitPeriodStatusEvent(
        tenant_id=tenant_id,
        benefit_period_id=benefit_period_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        created_by=actor_user_id,
        reason=reason,
        previous_value=previous_value,
        new_value=new_value,
        related_certification_id=related_certification_id,
    )
    db.add(event)
    return event


def rollover_benefit_period(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    election_date: date,
    start_date: date,
    benefit_type: AllowedBenefitType,
    actor_user_id: UUID,
) -> BenefitPeriod:
    """
    Enterprise-grade benefit period rollover.

    Guarantees:
    - Only one current benefit period per patient
    - Old current BP is closed before new BP becomes current
    - Safe retry behavior for the same rollover request
    - Runs inside a single DB transaction
    - Every create/rollover writes an immutable, actor-attributed
      BenefitPeriodStatusEvent in the same transaction (Eligibility
      Traceability Epic, Workstream 1) -- closing the previously
      confirmed Audit Gap and Attribution Gap for BenefitPeriod.

    `actor_user_id` is required (not optional): no benefit-period
    lifecycle action may be recorded without a real actor.
    """

    if benefit_type not in ("INITIAL", "RECERT"):
        raise ValueError("benefit_type must be 'INITIAL' or 'RECERT'")

    # Normalize identifiers to real UUID objects up front. Callers pass
    # either str or UUID for tenant_id/patient_id (both are accepted at
    # the DB-filter level since SQLAlchemy/psycopg2 cast strings
    # transparently there). But the idempotency check below compares
    # already-loaded ORM attribute values using plain Python `==`, which
    # does NOT consider `UUID('...') == 'same-string'` equal. Across a
    # fresh session (a real retried HTTP request, not the same in-process
    # object), a str tenant_id/patient_id would silently defeat the
    # idempotency check and create a duplicate benefit period on retry --
    # an audit-integrity break for this exact table. Normalizing here
    # closes that gap regardless of what type the caller passed in.
    if not isinstance(tenant_id, UUID):
        tenant_id = UUID(str(tenant_id))
    if not isinstance(patient_id, UUID):
        patient_id = UUID(str(patient_id))

    try:
        # ---------------------------------------------------------
        # 0. Tenant isolation guard: the patient must actually belong
        #    to the given tenant_id. Without this, a mismatched
        #    (tenant_id, patient_id) pair silently finds zero existing
        #    rows for that combination and proceeds to create a phantom
        #    benefit period scoped to the wrong tenant for a real
        #    patient it does not own -- a cross-tenant data-integrity
        #    break for an audit-critical table. Fail closed instead.
        # ---------------------------------------------------------
        patient_exists = (
            db.query(Patient.id)
            .filter(Patient.id == patient_id, Patient.tenant_id == tenant_id)
            .first()
        )
        if patient_exists is None:
            logger.warning(
                "benefit_period_rollover_denied_cross_tenant_or_unknown_patient "
                "tenant_id=%s patient_id=%s",
                tenant_id,
                patient_id,
            )
            raise ValueError("Patient not found for tenant.")

        # ---------------------------------------------------------
        # 1. Lock all BP rows for this patient/tenant
        # ---------------------------------------------------------
        existing_rows = (
            db.query(BenefitPeriod)
            .filter(
                BenefitPeriod.patient_id == patient_id,
                BenefitPeriod.tenant_id == tenant_id,
            )
            .with_for_update()
            .all()
        )

        # ---------------------------------------------------------
        # 2. Idempotency check
        # ---------------------------------------------------------
        for row in existing_rows:
            if (
                row.start_date == start_date
                and row.benefit_type == benefit_type
                and row.tenant_id == tenant_id
                and row.patient_id == patient_id
            ):
                return row

        # ---------------------------------------------------------
        # 3. Find current BP
        # ---------------------------------------------------------
        current_bp = next((r for r in existing_rows if r.is_current), None)
        previous_snapshot = _snapshot_benefit_period(current_bp)
        event_type = "ROLLED" if current_bp is not None else "CREATED"

        # ---------------------------------------------------------
        # 4. Validate chronology
        # ---------------------------------------------------------
        if current_bp and start_date < current_bp.start_date:
            raise ValueError(
                "start_date cannot be earlier than current BP start_date"
            )

        # ---------------------------------------------------------
        # 5. Compute next period number
        # ---------------------------------------------------------
        if not existing_rows:
            next_period_number = 1
        else:
            next_period_number = max(r.period_number for r in existing_rows) + 1

        # ---------------------------------------------------------
        # 6. Close current BP
        # ---------------------------------------------------------
        if current_bp:
            current_bp.is_current = False

            if current_bp.end_date is None:
                current_bp.end_date = start_date - timedelta(days=1)

        # ---------------------------------------------------------
        # 7. Compute CMS end date
        # ---------------------------------------------------------
        length_days = _cms_benefit_period_length_days(next_period_number)
        end_date = start_date + timedelta(days=length_days - 1)

        # ---------------------------------------------------------
        # 8. Create next/current BP
        # ---------------------------------------------------------
        new_bp = BenefitPeriod(
            tenant_id=tenant_id,
            patient_id=patient_id,
            benefit_type=benefit_type,
            period_number=next_period_number,
            election_date=election_date,
            start_date=start_date,
            end_date=end_date,
            is_current=True,
            created_by=actor_user_id,
        )

        db.add(new_bp)

        # ---------------------------------------------------------
        # 8a. Concurrency-safe idempotency backstop: two concurrent
        #    rollover attempts can both pass the in-memory idempotency
        #    check above (PostgreSQL READ COMMITTED does not retroactively
        #    surface a competing transaction's brand-new insert to an
        #    already-blocked query -- confirmed via a real two-session
        #    reproduction). The database-level unique constraint added
        #    alongside this change (migration v3w4x5y6z7a8) turns that
        #    race into a loud IntegrityError instead of a silent duplicate
        #    benefit period. Recover from it the same way the in-memory
        #    check would have: return the row the other transaction
        #    already committed.
        # ---------------------------------------------------------
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            logger.warning(
                "benefit_period_rollover_race_recovered tenant_id=%s "
                "patient_id=%s benefit_type=%s start_date=%s",
                tenant_id,
                patient_id,
                benefit_type,
                start_date,
            )
            winner = (
                db.query(BenefitPeriod)
                .filter(
                    BenefitPeriod.tenant_id == tenant_id,
                    BenefitPeriod.patient_id == patient_id,
                    BenefitPeriod.benefit_type == benefit_type,
                    BenefitPeriod.start_date == start_date,
                )
                .first()
            )
            if winner is None:
                # Not our own race after all -- some other integrity
                # constraint failed. Re-raise so it isn't silently
                # swallowed.
                raise
            return winner

        # ---------------------------------------------------------
        # 8b. Record the immutable audit-trail event (Workstream 1)
        # ---------------------------------------------------------
        record_benefit_period_event(
            db,
            tenant_id=tenant_id,
            benefit_period_id=new_bp.id,
            event_type=event_type,
            actor_user_id=actor_user_id,
            previous_value=previous_snapshot,
            new_value=_snapshot_benefit_period(new_bp),
        )

        # ---------------------------------------------------------
        # 9. Seed IDG_REVIEW task for the new BP
        # ---------------------------------------------------------
        idg_task = Task(
            tenant_id=tenant_id,
            patient_id=patient_id,
            benefit_period_id=new_bp.id,
            task_type=TaskType.IDG_REVIEW,
            origin=TaskOrigin.PERIODIC,
            discipline=TaskDiscipline.RN,
            regulatory_basis=TaskRegulatoryBasis.IDG_REVIEW,
            due_date=start_date + timedelta(days=14),
        )

        # Safe no-op if already linked
        attach_active_benefit_period_to_task(
            db,
            task=idg_task,
            tenant_id=tenant_id,
            patient_id=patient_id,
            as_of_date=idg_task.due_date,
        )

        db.add(idg_task)

        # ---------------------------------------------------------
        # 10. Commit atomically
        # ---------------------------------------------------------
        db.commit()

        return new_bp

    except Exception:
        db.rollback()
        raise