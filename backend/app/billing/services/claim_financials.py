"""
Shared per-claim financial aggregation.

Single source of truth for "claim net balance" so the Aging Report and the
Credit Balance Report never diverge on the underlying arithmetic:

    Claim Net Balance = Total Charges
                         - Posted Payments   (payments.paid_amount)
                         - Adjustments       (835 CAS lines, all group codes
                                              -- CO/PR/OA/PI/CR)
                         - Write-offs        (denials the biller marked
                                              WRITTEN_OFF instead of
                                              appealing)

    Net Balance > 0  -> outstanding / aging concern  (Aging Report)
    Net Balance < 0  -> overpayment / credit balance concern
                        (Credit Balance Report)
    Net Balance == 0 -> fully settled, not on either report

No new data store. Pure read-only aggregation over
app.billing.models.claim.Claim, app.billing.models.payment.Payment,
app.billing.models.payment_adjustment.PaymentAdjustment, and
app.billing.models.denial.Denial -- the same tables backing Claims
Management, Payment Posting, and Denials & Appeals.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.billing.models.claim import Claim
from app.billing.models.denial import Denial
from app.billing.models.payment import Payment
from app.billing.models.payment_adjustment import PaymentAdjustment
from app.billing.models.remittance_advice import RemittanceAdvice
from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet
from app.models.patient_payer import PatientPayer
from app.models.tenant import Tenant


def patient_display_name(
    first_name: str | None, middle_name: str | None, last_name: str | None
) -> str | None:
    parts = [p for p in (first_name, middle_name, last_name) if p]
    return " ".join(parts) if parts else None


@dataclass
class ClaimFinancialRow:
    claim_id: UUID
    tenant_id: UUID
    patient_id: UUID
    payer_name: str | None
    total_charge: Decimal
    status: str
    claim_control_number: str | None
    exported_at: datetime | None
    mrn: str | None
    patient_name: str | None
    posted_payments: Decimal
    adjustments: Decimal
    write_offs: Decimal
    payment_count: int
    # Real structured payer metadata (app.models.patient_payer.PatientPayer.
    # payer_type), matched by (patient_id, payer_name) -- NOT parsed/guessed
    # from the payer_name string. None when no matching PatientPayer record
    # exists, in which case classification must be treated as unverified
    # rather than assumed.
    payer_type: str | None
    # Patient-level payer responsibility (primary/secondary), resolved from
    # existing PatientPayer.priority_order / is_primary -- surfaced for
    # billing context only (e.g. a claim billed to Medicare may still show
    # the patient's Medi-Cal secondary here so a biller reviewing a credit
    # balance/refund/recoupment/reallocation knows who else has
    # responsibility). Not a new payer-accounting subsystem -- just an
    # existing-data lookup. None when not resolvable.
    primary_payer_name: str | None
    secondary_payer_name: str | None
    # "IF AVAILABLE" operational fields (billing context, from existing
    # data only -- Payment.remittance_advice.payer_name matched against
    # primary/secondary payer NAMES above; no new payer-to-payment link is
    # created). None/zero when nothing posted from that payer yet.
    primary_payer_paid: Decimal
    secondary_payer_paid: Decimal
    most_recent_payment_date: str | None

    @property
    def net_balance(self) -> Decimal:
        """Positive = outstanding (aging); negative = overpaid (credit)."""
        return self.total_charge - self.posted_payments - self.adjustments - self.write_offs


def load_claim_financials(
    db: Session,
    tenant_ids: list[UUID],
    *,
    require_exported: bool = False,
) -> list[ClaimFinancialRow]:
    """
    Load every claim for the given tenants with its posted-payments/
    adjustments/write-offs totals attached.

    Callers are responsible for all authorization (which tenant_ids the
    current user may view) -- this function only calculates.
    """
    if not tenant_ids:
        return []

    tenant_id_strs = [str(t) for t in tenant_ids]

    query = (
        db.query(
            Claim.id.label("claim_id"),
            Claim.tenant_id.label("tenant_id"),
            Claim.patient_id.label("patient_id"),
            Claim.payer_name.label("payer_name"),
            Claim.total_charge.label("total_charge"),
            Claim.status.label("status"),
            Claim.claim_control_number.label("claim_control_number"),
            Claim.exported_at.label("exported_at"),
            Patient.mrn.label("mrn"),
            PatientFaceSheet.first_name.label("patient_first_name"),
            PatientFaceSheet.middle_name.label("patient_middle_name"),
            PatientFaceSheet.last_name.label("patient_last_name"),
        )
        .join(Patient, Patient.id == Claim.patient_id)
        .outerjoin(PatientFaceSheet, PatientFaceSheet.patient_id == Patient.id)
        .filter(Claim.tenant_id.in_(tenant_id_strs))
    )

    if require_exported:
        query = query.filter(Claim.exported_at.isnot(None))

    claim_rows = query.all()
    if not claim_rows:
        return []

    claim_ids = [r.claim_id for r in claim_rows]

    payments_by_claim: dict = dict(
        db.query(Payment.claim_id, func.coalesce(func.sum(Payment.paid_amount), 0))
        .filter(Payment.claim_id.in_(claim_ids))
        .group_by(Payment.claim_id)
        .all()
    )

    payment_counts_by_claim: dict = dict(
        db.query(Payment.claim_id, func.count(Payment.id))
        .filter(Payment.claim_id.in_(claim_ids))
        .group_by(Payment.claim_id)
        .all()
    )

    adjustments_by_claim: dict = dict(
        db.query(Payment.claim_id, func.coalesce(func.sum(PaymentAdjustment.amount), 0))
        .join(PaymentAdjustment, PaymentAdjustment.payment_id == Payment.id)
        .filter(Payment.claim_id.in_(claim_ids))
        .group_by(Payment.claim_id)
        .all()
    )

    write_offs_by_claim: dict = dict(
        db.query(Denial.claim_id, func.coalesce(func.sum(Denial.denied_amount), 0))
        .filter(Denial.claim_id.in_(claim_ids))
        .filter(Denial.status == "WRITTEN_OFF")
        .group_by(Denial.claim_id)
        .all()
    )

    # Per-claim, per-payer paid amounts -- matched via the posting
    # RemittanceAdvice's header payer_name (existing 835 data, no new
    # payer-to-payment link). Used only to surface "Primary Payer Paid" /
    # "Secondary Payer Paid" operational context alongside the patient's
    # on-file primary/secondary payer names.
    paid_by_claim_and_payer: dict[tuple, Decimal] = {}
    most_recent_payment_date_by_claim: dict = {}
    for claim_id, payer_name, paid_amount, payment_date in (
        db.query(Payment.claim_id, RemittanceAdvice.payer_name, Payment.paid_amount, Payment.payment_date)
        .join(RemittanceAdvice, RemittanceAdvice.id == Payment.remittance_advice_id)
        .filter(Payment.claim_id.in_(claim_ids))
        .all()
    ):
        key = (claim_id, _payer_name_key(payer_name))
        paid_by_claim_and_payer[key] = paid_by_claim_and_payer.get(key, Decimal("0")) + Decimal(str(paid_amount or 0))
        if payment_date and (
            claim_id not in most_recent_payment_date_by_claim
            or payment_date > most_recent_payment_date_by_claim[claim_id]
        ):
            most_recent_payment_date_by_claim[claim_id] = payment_date

    payer_type_lookup = _payer_type_lookup(db, [r.patient_id for r in claim_rows])
    payer_priority_lookup = _payer_priority_lookup(db, [r.patient_id for r in claim_rows])

    rows: list[ClaimFinancialRow] = []
    for r in claim_rows:
        primary_name, secondary_name = payer_priority_lookup.get(r.patient_id, (None, None))
        primary_paid = (
            paid_by_claim_and_payer.get((r.claim_id, _payer_name_key(primary_name)), Decimal("0"))
            if primary_name
            else Decimal("0")
        )
        secondary_paid = (
            paid_by_claim_and_payer.get((r.claim_id, _payer_name_key(secondary_name)), Decimal("0"))
            if secondary_name
            else Decimal("0")
        )
        rows.append(
            ClaimFinancialRow(
                claim_id=r.claim_id,
                tenant_id=r.tenant_id,
                patient_id=r.patient_id,
                payer_name=r.payer_name,
                total_charge=Decimal(str(r.total_charge or 0)),
                status=r.status,
                claim_control_number=r.claim_control_number,
                exported_at=r.exported_at,
                mrn=r.mrn,
                patient_name=patient_display_name(
                    r.patient_first_name, r.patient_middle_name, r.patient_last_name
                ),
                posted_payments=Decimal(str(payments_by_claim.get(r.claim_id, 0))),
                adjustments=Decimal(str(adjustments_by_claim.get(r.claim_id, 0))),
                write_offs=Decimal(str(write_offs_by_claim.get(r.claim_id, 0))),
                payment_count=int(payment_counts_by_claim.get(r.claim_id, 0)),
                payer_type=payer_type_lookup.get((r.patient_id, _payer_name_key(r.payer_name))),
                primary_payer_name=primary_name,
                secondary_payer_name=secondary_name,
                primary_payer_paid=primary_paid,
                secondary_payer_paid=secondary_paid,
                most_recent_payment_date=most_recent_payment_date_by_claim.get(r.claim_id),
            )
        )
    return rows


def _payer_name_key(payer_name: str | None) -> str:
    return (payer_name or "").strip().lower()


def _payer_type_lookup(db: Session, patient_ids: list[UUID]) -> dict[tuple, str | None]:
    """
    Real structured payer_type metadata from PatientPayer, matched by
    (patient_id, payer_name) -- this is existing system-of-record payer
    data, not a name-based guess. If a patient has more than one
    PatientPayer row with the same payer_name (e.g. re-verified over
    time), the most recently created one wins.
    """
    if not patient_ids:
        return {}
    lookup: dict[tuple, str | None] = {}
    rows = (
        db.query(PatientPayer.patient_id, PatientPayer.payer_name, PatientPayer.payer_type, PatientPayer.created_at)
        .filter(PatientPayer.patient_id.in_(patient_ids))
        .order_by(PatientPayer.created_at.asc())
        .all()
    )
    for patient_id, payer_name, payer_type, _created_at in rows:
        # ascending order + overwrite -> most recently created wins.
        lookup[(patient_id, _payer_name_key(payer_name))] = payer_type
    return lookup


def _payer_priority_lookup(db: Session, patient_ids: list[UUID]) -> dict[UUID, tuple]:
    """
    Primary/secondary payer NAMES for billing-context display only (e.g.
    Credit Balance Report), resolved entirely from existing PatientPayer
    fields -- PatientPayer.priority_order (1=primary, 2=secondary, ...)
    when populated, falling back to PatientPayer.is_primary for the
    primary slot when priority_order isn't set. This is NOT a new payer
    hierarchy engine -- it reads the same coordination-of-benefits fields
    app.billing.services.msp_validation_service already relies on, and
    resolves nothing beyond "what is this patient's primary/secondary
    payer name right now".

    Returns {patient_id: (primary_payer_name | None, secondary_payer_name | None)}.
    """
    if not patient_ids:
        return {}

    rows = (
        db.query(
            PatientPayer.patient_id,
            PatientPayer.payer_name,
            PatientPayer.is_primary,
            PatientPayer.priority_order,
            PatientPayer.created_at,
        )
        .filter(PatientPayer.patient_id.in_(patient_ids))
        .all()
    )

    by_patient: dict[UUID, list] = {}
    for patient_id, payer_name, is_primary, priority_order, created_at in rows:
        by_patient.setdefault(patient_id, []).append((payer_name, is_primary, priority_order, created_at))

    result: dict[UUID, tuple] = {}
    for patient_id, payers in by_patient.items():
        by_priority = {p[2]: p for p in payers if p[2] is not None}
        primary = by_priority.get(1)
        secondary = by_priority.get(2)

        if primary is None:
            primary_candidates = [p for p in payers if p[1]]
            if primary_candidates:
                primary = max(primary_candidates, key=lambda p: p[3] or datetime.min)

        if secondary is None:
            remaining = [p for p in payers if p != primary]
            if remaining:
                secondary = min(remaining, key=lambda p: p[3] or datetime.min)

        result[patient_id] = (
            primary[0] if primary else None,
            secondary[0] if secondary else None,
        )

    return result


def resolve_primary_secondary_payer_names(db: Session, patient_id: UUID) -> tuple:
    """Single-patient convenience wrapper around _payer_priority_lookup (used
    by the case-detail endpoint, which only needs one patient's payer
    responsibility context)."""
    return _payer_priority_lookup(db, [patient_id]).get(patient_id, (None, None))


def find_potential_duplicate_payment_claim_ids(db: Session, claim_ids: list[UUID]) -> set:
    """
    Mechanical detection only: claims with 2+ posted Payment rows sharing
    the exact same nonzero paid_amount. This flags "Potential Duplicate
    Payment" for review -- it does NOT diagnose root cause. A biller must
    review and record the real reason (duplicate payment, posting error,
    COB issue, MSP issue, recoupment timing, or other) via the case
    action's reason_code -- see
    credit_balance_case_service.DUPLICATE_PAYMENT_REASON_CODES.
    """
    if not claim_ids:
        return set()
    rows = (
        db.query(Payment.claim_id)
        .filter(Payment.claim_id.in_(claim_ids))
        .filter(Payment.paid_amount != 0)
        .group_by(Payment.claim_id, Payment.paid_amount)
        .having(func.count(Payment.id) > 1)
        .all()
    )
    return {r[0] for r in rows}


def resolve_payer_type_for_claim(db: Session, patient_id: UUID, payer_name: str | None) -> str | None:
    """Single-claim convenience wrapper around _payer_type_lookup (used by the
    create-case endpoint, which only needs one claim's payer_type)."""
    return _payer_type_lookup(db, [patient_id]).get((patient_id, _payer_name_key(payer_name)))


def agency_display_names(db: Session, tenant_ids: list[UUID]) -> dict[str, str]:
    if not tenant_ids:
        return {}
    tenant_id_strs = [str(t) for t in tenant_ids]
    return {
        str(t.id): (t.display_name or t.legal_name)
        for t in db.query(Tenant.id, Tenant.display_name, Tenant.legal_name)
        .filter(Tenant.id.in_(tenant_id_strs))
        .all()
    }
