"""
Phase 4 - Billing Architecture Validation.

These tests exist to produce PROOF OF BEHAVIOR for two specific findings
from the billing audit (docs/planning/billing_inventory_and_gap_analysis.md)
that were previously classified from reading code alone. Each test calls
the real, unmodified production function against a real row in the
isolated test database and asserts on the actually-committed result --
not a re-implementation or mock of the logic under test.

Finding A: app.billing.api.claim_status_router.update_claim_status
enforces ALLOWED_TRANSITIONS, but app.billing.api.billing_router.
export_patient_claim_edi writes claim.status = "SENT" unconditionally.
Proven here by calling both real functions against the same claim.

Finding B: app.services.payment_service.post_payments_from_835 is a real,
reachable (POST /billing/835/upload) payment-ingestion path -- contrary to
the audit's original "no ingestion path found" conclusion, which was a
blind spot from only searching app/billing/ and missing app/services/.
Proven here by calling the real function with a synthetic parsed-835
payload and asserting the real Payment/RemittanceAdvice/Denial rows and
claim status transitions it commits.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.billing.api.claim_status_router import update_claim_status
from app.billing.models.payment import Payment
from app.billing.models.remittance_advice import RemittanceAdvice
from app.billing.models.denial import Denial
from app.services.payment_service import post_payments_from_835
from tests.test_aging_report_service import (
    _enable_billing_for_tenant,
    _make_billing_cycle,
    _make_claim,
    _make_patient,
)


@pytest.fixture()
def billing_enabled_tenant(db_session, tenant):
    return uuid.UUID(
        str(
            _enable_billing_for_tenant(
                db_session, uuid.UUID(str(tenant.id)), legal_name="Phase 4 Validation Agency"
            ).id
        )
    )


# ---------------------------------------------------------------------
# Finding A: Claim.status enforcement -- proven by real execution
# ---------------------------------------------------------------------

def test_claim_status_router_enforces_allowed_transitions_for_real(db_session, billing_enabled_tenant):
    """
    Proof that the status-transition endpoint itself is a real, working
    guard: a PAID claim (terminal state) cannot be moved anywhere,
    confirmed by actually calling the endpoint and getting a real 409.
    """
    cycle = _make_billing_cycle(db_session, billing_enabled_tenant, month=4)
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="P4A")
    claim = _make_claim(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("500.00"),
        exported_days_ago=10,
    )

    with pytest.raises(HTTPException) as exc_info:
        update_claim_status(
            payload={
                "patient_id": str(patient.id),
                "billing_cycle_id": str(cycle.id),
                "status": "SENT",
            },
            db=db_session,
        )

    assert exc_info.value.status_code == 409

    db_session.refresh(claim)
    assert claim.status == "PAID", (
        "Real proof: the enforced-transition endpoint correctly refuses "
        "to move a PAID claim back to SENT."
    )


def test_export_patient_claim_edi_bypasses_allowed_transitions_for_real(db_session, billing_enabled_tenant):
    """
    Proof (not inference) that app.billing.api.billing_router.
    export_patient_claim_edi writes claim.status = "SENT" directly,
    with no reference to ALLOWED_TRANSITIONS, by actually invoking the
    real endpoint function against a claim that is already PAID (a
    terminal state per claim_status_router.ALLOWED_TRANSITIONS) and
    observing the real committed status afterward.

    The heavy collaborators (claim-export payload construction, EDI text
    generation, file save) are stubbed to isolated, already-independently
    -tested return values so this test exercises only the status-write
    behavior of the real function body -- it does not reimplement any
    billing logic.
    """
    from app.billing.api import billing_router as billing_router_module

    cycle = _make_billing_cycle(db_session, billing_enabled_tenant, month=4)
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="P4B")
    claim = _make_claim(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("500.00"),
        exported_days_ago=10,
    )

    fake_export_payload = {
        "claim_header": {
            "claim_control_number": "CCN-BYPASS-TEST",
            "tenant_id": str(billing_enabled_tenant),
        },
    }

    class _FakePayload:
        patient_id = str(patient.id)
        billing_cycle_id = str(cycle.id)
        override_used = False
        override_reason = None

    class _FakeUser:
        tenant_id = str(billing_enabled_tenant)

    with patch.object(
        billing_router_module, "build_patient_claim_export", return_value=fake_export_payload
    ), patch.object(
        billing_router_module, "validate_claim", return_value={"errors": [], "warnings": []}
    ), patch.object(
        billing_router_module, "build_837i_text", return_value="FAKE-EDI-TEXT"
    ), patch.object(
        billing_router_module, "save_edi_to_file", return_value="/tmp/fake-edi.txt"
    ), patch.object(
        billing_router_module, "require_automated_billing", return_value=None
    ):
        billing_router_module.export_patient_claim_edi(
            payload=_FakePayload(),
            db=db_session,
            user=_FakeUser(),
        )

    db_session.refresh(claim)
    assert claim.status == "SENT", (
        "CONFIRMED BUG (behavioral proof, not inference): calling the "
        "real export_patient_claim_edi endpoint against a claim that was "
        "already PAID (terminal per ALLOWED_TRANSITIONS) silently "
        "overwrote its status back to SENT. This bypasses the same "
        "enforcement that update_claim_status correctly applies (see the "
        "sibling test above, which proves the enforced path DOES refuse "
        "this exact transition)."
    )


# ---------------------------------------------------------------------
# Finding B: 835 payment ingestion -- proven real and reachable
# ---------------------------------------------------------------------

def test_post_payments_from_835_ingests_real_payment_and_pays_claim(db_session, billing_enabled_tenant):
    """
    Proof that app.services.payment_service.post_payments_from_835 (wired
    to a real, registered endpoint at POST /billing/835/upload via
    app.api.billing_835) is a real payment-ingestion path: calling it with
    a synthetic parsed-835 payload against a real SENT claim actually
    creates a RemittanceAdvice row, a matched Payment row, and correctly
    advances the claim to PAID.
    """
    cycle = _make_billing_cycle(db_session, billing_enabled_tenant, month=5)
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="P4C")
    claim = _make_claim(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="SENT",
        payer_name="Medicare",
        total_charge=Decimal("500.00"),
        exported_days_ago=5,
    )
    claim.claim_control_number = "CCN-835-TEST"
    db_session.commit()

    parsed = {
        "payer_name": "Medicare",
        "total_paid_amount": 500.00,
        "payment_date": "20260410",
        "claims": [
            {
                "claim_control_number": "CCN-835-TEST",
                "patient_name": "Test Patient",
                "billed_amount": 500.00,
                "paid_amount": 500.00,
                "patient_responsibility": 0.00,
                "payment_date": "20260410",
                "adjustments": [],
            }
        ],
    }

    remittance = post_payments_from_835(
        db=db_session,
        tenant_id=str(billing_enabled_tenant),
        parsed=parsed,
        file_name="test-835.txt",
        raw_content="FAKE-835-CONTENT",
    )

    assert remittance.id is not None
    ra_row = db_session.get(RemittanceAdvice, remittance.id)
    assert ra_row is not None and ra_row.status == "POSTED"

    payment_row = (
        db_session.query(Payment)
        .filter(Payment.remittance_advice_id == remittance.id)
        .one()
    )
    assert payment_row.match_status == "MATCHED"
    assert payment_row.claim_id == claim.id
    assert Decimal(str(payment_row.paid_amount)) == Decimal("500.00")

    db_session.refresh(claim)
    assert claim.status == "PAID", (
        "Real proof: a matched, non-denied 835 payment correctly advances "
        "a SENT claim to PAID."
    )


def test_post_payments_from_835_denies_claim_on_denial_carc_and_respects_status_guard(
    db_session, billing_enabled_tenant
):
    """
    Proof of two behaviors in the same real function call:
    1. A denial CARC code (96) on a $0-paid line creates a real Denial
       row and moves the claim to DENIED.
    2. Unlike export_patient_claim_edi, this function DOES guard its
       status write -- it only transitions claims that are still in
       SENT/ACCEPTED, so a second payment posted against an already
       terminal claim cannot silently corrupt it. Proven by posting a
       second 835 payment against the now-DENIED claim and confirming the
       status does not move again.
    """
    cycle = _make_billing_cycle(db_session, billing_enabled_tenant, month=6)
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="P4D")
    claim = _make_claim(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="SENT",
        payer_name="Medicare",
        total_charge=Decimal("300.00"),
        exported_days_ago=5,
    )
    claim.claim_control_number = "CCN-835-DENY-TEST"
    db_session.commit()

    denial_parsed = {
        "payer_name": "Medicare",
        "total_paid_amount": 0.00,
        "payment_date": "20260415",
        "claims": [
            {
                "claim_control_number": "CCN-835-DENY-TEST",
                "patient_name": "Test Patient",
                "billed_amount": 300.00,
                "paid_amount": 0.00,
                "patient_responsibility": 0.00,
                "payment_date": "20260415",
                "adjustments": [{"group_code": "CO", "carc_code": "96", "amount": 300.00}],
            }
        ],
    }

    post_payments_from_835(
        db=db_session,
        tenant_id=str(billing_enabled_tenant),
        parsed=denial_parsed,
        file_name="test-835-denial.txt",
        raw_content="FAKE-835-DENIAL-CONTENT",
    )

    db_session.refresh(claim)
    assert claim.status == "DENIED"

    denial_row = db_session.query(Denial).filter(Denial.claim_id == claim.id).one()
    assert denial_row.carc_code == "96"
    assert denial_row.status == "OPEN"

    # Post a second (e.g. corrected/duplicate) remittance against the same
    # now-DENIED claim and confirm the real status guard holds.
    second_parsed = {
        "payer_name": "Medicare",
        "total_paid_amount": 300.00,
        "payment_date": "20260420",
        "claims": [
            {
                "claim_control_number": "CCN-835-DENY-TEST",
                "patient_name": "Test Patient",
                "billed_amount": 300.00,
                "paid_amount": 300.00,
                "patient_responsibility": 0.00,
                "payment_date": "20260420",
                "adjustments": [],
            }
        ],
    }
    post_payments_from_835(
        db=db_session,
        tenant_id=str(billing_enabled_tenant),
        parsed=second_parsed,
        file_name="test-835-second.txt",
        raw_content="FAKE-835-SECOND-CONTENT",
    )

    db_session.refresh(claim)
    assert claim.status == "DENIED", (
        "Real proof: post_payments_from_835 only transitions claims that "
        "are still SENT/ACCEPTED -- a claim already moved to a terminal "
        "state (DENIED here) is left alone by a later posting, unlike "
        "export_patient_claim_edi's unconditional status write."
    )
