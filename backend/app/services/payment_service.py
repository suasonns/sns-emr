from __future__ import annotations

from datetime import date, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.billing.models.claim import Claim
from app.billing.models.payment import Payment
from app.billing.models.payment_adjustment import PaymentAdjustment
from app.billing.models.remittance_advice import RemittanceAdvice
from app.billing.models.denial import Denial

# Default appeal filing window used when a payer-specific deadline isn't
# configured elsewhere. Medicare's standard reconsideration window is 120
# days from the remittance date -- used as a safe, documented default.
DEFAULT_APPEAL_WINDOW_DAYS = 120

# Human-readable descriptions for the denial CARC codes we detect, so the
# Denial row carries a real reason string instead of a bare code.
DENIAL_CARC_DESCRIPTIONS = {
    "1": "Deductible amount",
    "16": "Claim/service lacks information needed for adjudication",
    "18": "Exact duplicate claim/service",
    "29": "The time limit for filing has expired",
    "50": "Non-covered service, not deemed medical necessity",
    "96": "Non-covered charge(s)",
    "109": "Claim not covered by this payer/contractor",
    "197": "Precertification/authorization absent",
}


def _parse_835_date(raw: str | None) -> date | None:
    """Parses an 835 CCYYMMDD date string into a date, if present/valid."""
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y%m%d").date()
    except ValueError:
        return None

# CARC codes that represent a hard denial (zero-pay, not just a
# contractual write-off). This list intentionally starts small/explicit
# rather than guessing -- extend it as real denial reasons are seen.
DENIAL_CARC_CODES = {
    "1",  # Deductible amount
    "16",  # Claim/service lacks information needed for adjudication
    "18",  # Exact duplicate claim/service
    "29",  # The time limit for filing has expired
    "50",  # Non-covered service, not deemed medical necessity
    "96",  # Non-covered charge(s)
    "109",  # Claim not covered by this payer/contractor
    "197",  # Precertification/authorization absent
}


def _is_denied(paid_amount: float | None, adjustments: list[dict]) -> bool:
    if paid_amount not in (None, 0, 0.0):
        return False
    return any(adj.get("carc_code") in DENIAL_CARC_CODES for adj in adjustments)


def post_payments_from_835(
    db: Session,
    tenant_id: str,
    parsed: dict,
    file_name: str | None = None,
    raw_content: str | None = None,
) -> RemittanceAdvice:
    """
    Persists a parsed 835 (see app.services.edi_835_parser.parse_835_file)
    as a RemittanceAdvice header + one Payment row per CLP claim, each
    with its PaymentAdjustment (CARC) lines. Matches each payment to a
    real Claim by claim_control_number when possible and advances the
    claim's lifecycle status (PAID / DENIED) accordingly -- never
    silently drops an unmatched payment, it is posted with
    match_status="UNMATCHED" for manual reconciliation instead.
    """
    claims_data = parsed.get("claims", [])

    remittance = RemittanceAdvice(
        id=str(uuid4()),
        tenant_id=tenant_id,
        payer_name=parsed.get("payer_name"),
        total_paid_amount=parsed.get("total_paid_amount"),
        payment_date=parsed.get("payment_date"),
        claim_count=len(claims_data),
        file_name=file_name,
        raw_content=raw_content,
        status="POSTED",
    )
    db.add(remittance)
    db.flush()

    for item in claims_data:
        claim_control_number = item.get("claim_control_number")
        matched_claim = None
        if claim_control_number:
            matched_claim = db.execute(
                select(Claim).where(
                    Claim.tenant_id == tenant_id,
                    Claim.claim_control_number == claim_control_number,
                )
            ).scalar_one_or_none()

        adjustments = item.get("adjustments", [])
        denied = _is_denied(item.get("paid_amount"), adjustments)

        payment = Payment(
            id=str(uuid4()),
            tenant_id=tenant_id,
            remittance_advice_id=remittance.id,
            claim_id=matched_claim.id if matched_claim else None,
            claim_control_number=claim_control_number,
            patient_name=item.get("patient_name"),
            billed_amount=item.get("billed_amount"),
            allowed_amount=item.get("billed_amount"),
            paid_amount=item.get("paid_amount"),
            patient_responsibility=item.get("patient_responsibility"),
            payment_date=item.get("payment_date") or parsed.get("payment_date"),
            is_denied=denied,
            match_status="MATCHED" if matched_claim else "UNMATCHED",
        )
        db.add(payment)
        db.flush()

        for adj in adjustments:
            db.add(
                PaymentAdjustment(
                    id=str(uuid4()),
                    payment_id=payment.id,
                    group_code=adj.get("group_code"),
                    carc_code=adj.get("carc_code"),
                    amount=adj.get("amount"),
                )
            )

        if matched_claim is not None:
            if denied and matched_claim.status in ("SENT", "ACCEPTED"):
                matched_claim.status = "DENIED"
                matched_claim.last_status_reason = (
                    f"Denied via 835 remittance ({', '.join(a['carc_code'] for a in adjustments if a.get('carc_code'))})"
                )
            elif not denied and matched_claim.status in ("SENT", "ACCEPTED"):
                matched_claim.status = "PAID"
                matched_claim.last_status_reason = "Paid via 835 remittance"

        if denied and matched_claim is not None:
            denial_carc = next(
                (
                    a.get("carc_code")
                    for a in adjustments
                    if a.get("carc_code") in DENIAL_CARC_CODES
                ),
                None,
            )
            payment_date = _parse_835_date(
                item.get("payment_date") or parsed.get("payment_date")
            )
            billed = item.get("billed_amount")
            paid = item.get("paid_amount") or 0
            denied_amount = (billed - paid) if billed is not None else None

            db.add(
                Denial(
                    id=str(uuid4()),
                    tenant_id=tenant_id,
                    claim_id=matched_claim.id,
                    payment_id=payment.id,
                    carc_code=denial_carc,
                    reason_description=DENIAL_CARC_DESCRIPTIONS.get(denial_carc),
                    denied_amount=denied_amount,
                    denial_date=payment_date,
                    appeal_deadline=(
                        payment_date + timedelta(days=DEFAULT_APPEAL_WINDOW_DAYS)
                        if payment_date
                        else None
                    ),
                    status="OPEN",
                )
            )

    db.commit()

    return remittance

