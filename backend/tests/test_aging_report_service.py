from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.billing.scope import resolve_multi_agency_tenant_ids as _resolve_scope_tenant_ids
from app.billing.models.billing_cycle import BillingCycle
from app.billing.models.claim import Claim
from app.billing.models.denial import Denial
from app.billing.models.payment import Payment
from app.billing.models.payment_adjustment import PaymentAdjustment
from app.billing.models.remittance_advice import RemittanceAdvice
from app.billing.services.aging_report_service import AGING_BUCKETS, build_ar_aging_report
from app.core.security import create_access_token
from app.models.patient import Patient
from app.models.tenant import Tenant
from tests.conftest import TEST_USER_ID


def _headers(role: str, tenant_id: uuid.UUID) -> dict[str, str]:
    token = create_access_token(
        user_id=TEST_USER_ID,
        role=role,
        tenant_id=tenant_id,
        email=f"{role.lower()}@example.com",
    )
    return {"Authorization": f"Bearer {token}"}


def _enable_billing_for_tenant(db_session, tenant_id: uuid.UUID, *, legal_name: str) -> Tenant:
    tenant = db_session.get(Tenant, tenant_id)
    if tenant is None:
        tenant = Tenant(
            id=tenant_id,
            legal_name=legal_name,
            display_name=legal_name,
            npi=f"{str(tenant_id.int)[:10]:0>10}",
            tenant_type="DEV",
            status="ACTIVE",
        )
        db_session.add(tenant)
    tenant.legal_name = legal_name
    tenant.display_name = legal_name
    tenant.tenant_type = "DEV"
    tenant.status = "ACTIVE"
    tenant.billing_enabled = True
    tenant.ein = "123456789"
    tenant.ptan = f"P{str(tenant_id.int)[:7]}"
    db_session.commit()
    return tenant


def _make_patient(db_session, tenant_id: uuid.UUID, *, mrn_prefix: str) -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"{mrn_prefix}-{uuid.uuid4().hex[:8]}",
        date_of_birth=date(1946, 6, 6),
        primary_diagnosis="J44.9",
        status="ACTIVE",
        election_signed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_billing_cycle(db_session, tenant_id: uuid.UUID, *, month: int, year: int = 2026) -> BillingCycle:
    cycle = BillingCycle(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        month=month,
        year=year,
        start_date=date(year, month, 1),
        end_date=date(year, month, 28),
        status="OPEN",
        created_by="test-suite",
    )
    db_session.add(cycle)
    db_session.commit()
    return cycle


def _make_claim(
    db_session,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    billing_cycle_id: uuid.UUID,
    status: str,
    payer_name: str,
    total_charge: Decimal,
    exported_days_ago: int | None,
) -> Claim:
    claim = Claim(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        billing_cycle_id=billing_cycle_id,
        payer_name=payer_name,
        service_date=date(2026, 1, 15),
        total_charge=total_charge,
        total_units=4,
        risk_score=0,
        status=status,
        exported_at=(
            datetime.now(timezone.utc) - timedelta(days=exported_days_ago)
            if exported_days_ago is not None
            else None
        ),
        created_by="test-suite",
    )
    db_session.add(claim)
    db_session.commit()
    return claim


def _make_remittance(db_session, tenant_id: uuid.UUID, *, payer_name: str = "Medicare", payment_date: str = "20260301") -> RemittanceAdvice:
    ra = RemittanceAdvice(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        payer_name=payer_name,
        total_paid_amount=Decimal("0.00"),
        payment_date=payment_date,
        claim_count=1,
        status="POSTED",
    )
    db_session.add(ra)
    db_session.commit()
    return ra


def _make_payment(
    db_session,
    *,
    tenant_id: uuid.UUID,
    remittance_advice_id: uuid.UUID,
    claim_id: uuid.UUID,
    paid_amount: Decimal,
    payment_date: str | None = None,
) -> Payment:
    payment = Payment(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        remittance_advice_id=remittance_advice_id,
        claim_id=claim_id,
        paid_amount=paid_amount,
        payment_date=payment_date,
        match_status="MATCHED",
    )
    db_session.add(payment)
    db_session.commit()
    return payment


def _make_adjustment(db_session, *, payment_id: uuid.UUID, group_code: str, carc_code: str, amount: Decimal) -> None:
    db_session.add(
        PaymentAdjustment(
            id=uuid.uuid4(),
            payment_id=payment_id,
            group_code=group_code,
            carc_code=carc_code,
            amount=amount,
        )
    )
    db_session.commit()


def _make_written_off_denial(db_session, *, tenant_id: uuid.UUID, claim_id: uuid.UUID, amount: Decimal) -> None:
    db_session.add(
        Denial(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            claim_id=claim_id,
            carc_code="P1",
            denied_amount=amount,
            denial_date=date(2026, 3, 1),
            status="WRITTEN_OFF",
        )
    )
    db_session.commit()


def test_aging_buckets_are_the_standard_five():
    assert AGING_BUCKETS == ["0-30", "31-60", "61-90", "91-120", "120+"]


def test_outstanding_balance_formula_and_bucketing(db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Aging Test Hospice")
    cycle = _make_billing_cycle(db_session, tenant_id, month=3)

    # Claim 1: submitted 15 days ago, partially paid + adjusted -> real
    # outstanding balance, lands in the 0-30 bucket.
    patient1 = _make_patient(db_session, tenant_id, mrn_prefix="AGE1")
    claim1 = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient1.id,
        billing_cycle_id=cycle.id,
        status="SENT",
        payer_name="Medicare",
        total_charge=Decimal("1000.00"),
        exported_days_ago=15,
    )
    ra = _make_remittance(db_session, tenant_id)
    payment1 = _make_payment(
        db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim1.id, paid_amount=Decimal("600.00")
    )
    _make_adjustment(db_session, payment_id=payment1.id, group_code="CO", carc_code="45", amount=Decimal("150.00"))
    # 1000 - 600 - 150 = 250 outstanding, 15 days -> bucket 0-30

    # Claim 2: submitted 95 days ago, no payments/adjustments at all ->
    # full charge outstanding, lands in the 91-120 bucket.
    patient2 = _make_patient(db_session, tenant_id, mrn_prefix="AGE2")
    claim2 = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient2.id,
        billing_cycle_id=cycle.id,
        status="SENT",
        payer_name="Aetna",
        total_charge=Decimal("500.00"),
        exported_days_ago=95,
    )
    # 500 - 0 - 0 - 0 = 500 outstanding, 95 days -> bucket 91-120

    # Claim 3: submitted 200 days ago, fully paid and fully written off ->
    # ZERO outstanding, must be EXCLUDED entirely (not a collection concern).
    patient3 = _make_patient(db_session, tenant_id, mrn_prefix="AGE3")
    claim3 = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient3.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("800.00"),
        exported_days_ago=200,
    )
    payment3 = _make_payment(
        db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim3.id, paid_amount=Decimal("650.00")
    )
    _make_written_off_denial(db_session, tenant_id=tenant_id, claim_id=claim3.id, amount=Decimal("150.00"))
    # 800 - 650 - 0 - 150 = 0 outstanding -> excluded

    # Claim 4: never submitted (no exported_at) -> excluded, no aging clock.
    patient4 = _make_patient(db_session, tenant_id, mrn_prefix="AGE4")
    _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient4.id,
        billing_cycle_id=cycle.id,
        status="READY",
        payer_name="Medicare",
        total_charge=Decimal("300.00"),
        exported_days_ago=None,
    )

    report = build_ar_aging_report(db_session, [tenant_id])

    assert report["summary"]["claim_count"] == 2
    assert report["summary"]["total_outstanding"] == "750.00"

    by_claim_id = {c["claim_id"]: c for c in report["claims"]}
    assert str(claim1.id) in by_claim_id
    assert str(claim2.id) in by_claim_id
    assert str(claim3.id) not in by_claim_id  # zero balance, excluded

    row1 = by_claim_id[str(claim1.id)]
    assert row1["outstanding_balance"] == "250.00"
    assert row1["bucket"] == "0-30"
    assert row1["posted_payments"] == "600.00"
    assert row1["adjustments"] == "150.00"

    row2 = by_claim_id[str(claim2.id)]
    assert row2["outstanding_balance"] == "500.00"
    assert row2["bucket"] == "91-120"

    bucket_map = {b["bucket"]: b for b in report["by_bucket"]}
    assert bucket_map["0-30"]["total_outstanding"] == "250.00"
    assert bucket_map["0-30"]["claim_count"] == 1
    assert bucket_map["91-120"]["total_outstanding"] == "500.00"
    assert bucket_map["91-120"]["claim_count"] == 1
    assert bucket_map["31-60"]["claim_count"] == 0
    assert bucket_map["61-90"]["claim_count"] == 0
    assert bucket_map["120+"]["claim_count"] == 0

    payer_map = {p["payer_name"]: p for p in report["by_payer"]}
    assert payer_map["Medicare"]["total_outstanding"] == "250.00"
    assert payer_map["Aetna"]["total_outstanding"] == "500.00"

    agency_map = {a["tenant_id"]: a for a in report["by_agency"]}
    assert agency_map[str(tenant_id)]["total_outstanding"] == "750.00"
    assert agency_map[str(tenant_id)]["claim_count"] == 2


def test_no_tenant_ids_returns_empty_report(db_session):
    report = build_ar_aging_report(db_session, [])
    assert report["summary"]["claim_count"] == 0
    assert report["summary"]["total_outstanding"] == "0.00"
    assert report["claims"] == []
    assert {b["bucket"] for b in report["by_bucket"]} == set(AGING_BUCKETS)


def test_aging_report_endpoint_single_agency(client, db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Endpoint Aging Hospice")
    cycle = _make_billing_cycle(db_session, tenant_id, month=3)
    patient = _make_patient(db_session, tenant_id, mrn_prefix="EPAGE")
    _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="SENT",
        payer_name="Medicare",
        total_charge=Decimal("400.00"),
        exported_days_ago=40,
    )

    response = client.get(
        "/billing/aging-report",
        headers=_headers("BILLING", tenant_id),
        params={"tenant_id": str(tenant_id)},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["summary"]["claim_count"] == 1
    assert payload["summary"]["total_outstanding"] == "400.00"
    assert payload["claims"][0]["bucket"] == "31-60"


def test_resolve_scope_tenant_ids_all_agencies_requires_billing_scope(db_session, tenant):
    """
    Non-billing (ordinary tenant) users always resolve to exactly their own
    tenant, regardless of an all_agencies=true request -- the aggregate
    "All Assigned Agencies" view only applies to billing-department staff,
    per the approved 2026-09-05 aging report directive.
    """
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Scope Test Hospice")

    class _FakeUser:
        role = "RN"

    fake_user = _FakeUser()
    fake_user.tenant_id = tenant_id

    resolved = _resolve_scope_tenant_ids(db_session, fake_user, None, None, True)
    assert resolved == [tenant_id]
