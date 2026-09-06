from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.billing.models.facility_collection_alert import FacilityCollectionAlert
from app.billing.models.facility_payment_allocation import FacilityPaymentAllocation
from app.billing.models.facility_payment_audit_log import FacilityPaymentAuditLog
from app.billing.models.facility_payment_expectation import FacilityPaymentExpectation
from app.billing.models.patient_pos import PatientPOS
from app.billing.models.payment import Payment
from app.billing.models.remittance_advice import RemittanceAdvice
from app.billing.services import facility_payment_service
from app.models.patient_facesheet import PatientFaceSheet
from app.models.patient_payer import PatientPayer
from app.models.tenant import Tenant
from tests.conftest import TEST_USER_ID
from tests.test_aging_report_service import (
    _enable_billing_for_tenant,
    _headers,
    _make_billing_cycle,
    _make_claim,
    _make_patient,
    _make_payment,
    _make_remittance,
)


def _make_facesheet(db_session, tenant_id: uuid.UUID, patient_id: uuid.UUID, first_name: str, last_name: str) -> None:
    db_session.add(
        PatientFaceSheet(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            patient_id=patient_id,
            first_name=first_name,
            last_name=last_name,
            created_by=TEST_USER_ID,
        )
    )
    db_session.commit()


def _make_patient_payer(
    db_session,
    patient_id: uuid.UUID,
    *,
    payer_name: str,
    payer_type: str,
    priority_order: int | None = None,
    is_primary: bool | None = None,
    facility_name: str | None = None,
) -> PatientPayer:
    payer = PatientPayer(
        id=uuid.uuid4(),
        patient_id=patient_id,
        payer_name=payer_name,
        payer_type=payer_type,
        priority_order=priority_order,
        is_primary=is_primary,
        effective_start_date=date(2026, 1, 1),
        facility_name=facility_name,
        created_by=TEST_USER_ID,
    )
    db_session.add(payer)
    db_session.commit()
    return payer


def _make_patient_pos(
    db_session,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    *,
    pos_type: str,
    facility_name: str,
    effective_date: date,
    end_date: date | None = None,
    room_number: str | None = None,
    status: str = "ACTIVE",
) -> PatientPOS:
    pos = PatientPOS(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        pos_type=pos_type,
        facility_name=facility_name,
        room_number=room_number,
        effective_date=effective_date,
        end_date=end_date,
        status=status,
        created_by=str(TEST_USER_ID),
    )
    db_session.add(pos)
    db_session.commit()
    return pos


def _make_second_tenant(db_session, *, legal_name: str) -> uuid.UUID:
    tenant_id = uuid.uuid4()
    _enable_billing_for_tenant(db_session, tenant_id, legal_name=legal_name)
    return tenant_id


def _create_expectation(
    db_session,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    patient_pos_id: uuid.UUID | None = None,
    responsibility_category: str = "ROOM_AND_BOARD",
    expected_funding_source: str = "MEDICAID_FFS",
    expected_amount: str = "1000.00",
    service_period_start: date = date(2026, 3, 1),
    service_period_end: date = date(2026, 3, 31),
    due_date: date | None = date(2026, 4, 15),
    expected_payer_name_snapshot: str | None = "Medi-Cal",
    share_of_cost_amount: str | None = None,
    authorization_reference: str | None = None,
    contract_reference: str | None = None,
    notes: str | None = None,
    status: str = "ACTIVE",
    source: str = "AUTHORIZED_MANUAL_ENTRY",
    client_request_id: uuid.UUID | None = None,
) -> FacilityPaymentExpectation:
    return facility_payment_service.create_facility_payment_expectation(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_id,
        patient_pos_id=patient_pos_id,
        responsibility_category=responsibility_category,
        expected_funding_source=expected_funding_source,
        expected_amount=Decimal(expected_amount),
        service_period_start=service_period_start,
        service_period_end=service_period_end,
        due_date=due_date,
        authorization_reference=authorization_reference,
        contract_reference=contract_reference,
        expected_payer_name_snapshot=expected_payer_name_snapshot,
        share_of_cost_amount=Decimal(share_of_cost_amount) if share_of_cost_amount is not None else None,
        notes=notes,
        status=status,
        source=source,
        client_request_id=client_request_id,
        user_id=TEST_USER_ID,
        user_role="BILLING",
    )


def _make_unmatched_payment(
    db_session,
    *,
    tenant_id: uuid.UUID,
    remittance_advice_id: uuid.UUID,
    paid_amount: str,
    claim_control_number: str | None = None,
    payment_date: str = "20260320",
) -> Payment:
    payment = Payment(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        remittance_advice_id=remittance_advice_id,
        claim_id=None,
        claim_control_number=claim_control_number,
        patient_name="Unmatched Payment",
        paid_amount=Decimal(paid_amount),
        payment_date=payment_date,
        match_status="UNMATCHED",
    )
    db_session.add(payment)
    db_session.commit()
    return payment


@pytest.fixture()
def billing_enabled_tenant(db_session, tenant):
    return uuid.UUID(str(_enable_billing_for_tenant(db_session, uuid.UUID(str(tenant.id)), legal_name="Facility Visibility Agency").id))


def test_expectation_captures_snapshot_from_pos_and_payers(db_session, billing_enabled_tenant):
    cycle = _make_billing_cycle(db_session, billing_enabled_tenant, month=3)
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FVP1")
    _make_facesheet(db_session, billing_enabled_tenant, patient.id, "Sam", "Resident")
    pos = _make_patient_pos(
        db_session,
        billing_enabled_tenant,
        patient.id,
        pos_type="SNF",
        facility_name="Sunrise SNF",
        room_number="12B",
        effective_date=date(2026, 3, 1),
        end_date=date(2026, 3, 31),
    )
    _make_patient_payer(
        db_session,
        patient.id,
        payer_name="Medicare Hospice",
        payer_type="MEDICARE_HOSPICE",
        priority_order=1,
        is_primary=True,
    )
    _make_patient_payer(
        db_session,
        patient.id,
        payer_name="Medi-Cal",
        payer_type="MEDICAID",
        priority_order=2,
        is_primary=False,
    )
    expectation = _create_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        patient_pos_id=pos.id,
        expected_payer_name_snapshot="Medi-Cal",
    )

    assert cycle is not None
    assert expectation.facility_name_snapshot == "Sunrise SNF"
    assert expectation.residence_type_snapshot == "SNF"
    assert expectation.room_number_snapshot == "12B"
    assert expectation.primary_payer_name_snapshot == "Medicare Hospice"
    assert expectation.secondary_payer_name_snapshot == "Medi-Cal"
    assert expectation.expected_funding_source_snapshot == "MEDICAID_FFS"
    assert expectation.expected_payer_name_snapshot == "Medi-Cal"


def test_two_expectations_do_not_collapse_same_patient(db_session, billing_enabled_tenant):
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FVP2")
    pos = _make_patient_pos(
        db_session,
        billing_enabled_tenant,
        patient.id,
        pos_type="SNF",
        facility_name="Harbor SNF",
        effective_date=date(2026, 4, 1),
    )
    hospice = _create_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        patient_pos_id=pos.id,
        responsibility_category="HOSPICE_SERVICE",
        expected_funding_source="MEDICAID_MANAGED_CARE",
        expected_amount="500.00",
        expected_payer_name_snapshot="Managed Medi-Cal",
    )
    facility = _create_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        patient_pos_id=pos.id,
        responsibility_category="ROOM_AND_BOARD",
        expected_funding_source="MEDICAID_FFS",
        expected_amount="900.00",
        expected_payer_name_snapshot="Medi-Cal",
    )
    rows = db_session.query(FacilityPaymentExpectation).filter(FacilityPaymentExpectation.patient_id == patient.id).all()
    assert {row.responsibility_category for row in rows} == {"HOSPICE_SERVICE", "ROOM_AND_BOARD"}
    assert hospice.id != facility.id


def test_assisted_living_patient_responsibility_without_payer(db_session, billing_enabled_tenant):
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FVP3")
    pos = _make_patient_pos(
        db_session,
        billing_enabled_tenant,
        patient.id,
        pos_type="ALF",
        facility_name="Oak ALF",
        effective_date=date(2026, 2, 1),
    )
    expectation = _create_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        patient_pos_id=pos.id,
        responsibility_category="PATIENT_RESPONSIBILITY",
        expected_funding_source="PATIENT_RESPONSIBILITY",
        expected_amount="600.00",
        expected_payer_name_snapshot=None,
    )
    assert expectation.expected_payer_name_snapshot is None
    assert expectation.residence_type_snapshot == "ALF"


def test_share_of_cost_expectation_records_share_amount(db_session, billing_enabled_tenant):
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FVP4")
    pos = _make_patient_pos(
        db_session,
        billing_enabled_tenant,
        patient.id,
        pos_type="BOARD_AND_CARE",
        facility_name="Garden Board and Care",
        effective_date=date(2026, 5, 1),
    )
    expectation = _create_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        patient_pos_id=pos.id,
        responsibility_category="SHARE_OF_COST",
        expected_funding_source="SHARE_OF_COST",
        expected_amount="450.00",
        expected_payer_name_snapshot=None,
        share_of_cost_amount="125.00",
    )
    assert Decimal(str(expectation.share_of_cost_amount)) == Decimal("125.00")


def test_confirmed_allocation_exact_amount_marks_paid(db_session, billing_enabled_tenant):
    cycle = _make_billing_cycle(db_session, billing_enabled_tenant, month=6)
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FVP5")
    pos = _make_patient_pos(db_session, billing_enabled_tenant, patient.id, pos_type="SNF", facility_name="Paid SNF", effective_date=date(2026, 6, 1))
    claim = _make_claim(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medi-Cal",
        total_charge=Decimal("1000.00"),
        exported_days_ago=1,
    )
    claim.claim_control_number = "FAC-PAID-1"
    db_session.commit()
    remittance = _make_remittance(db_session, billing_enabled_tenant, payer_name="Medi-Cal", payment_date="20260620")
    payment = _make_payment(
        db_session,
        tenant_id=billing_enabled_tenant,
        remittance_advice_id=remittance.id,
        claim_id=claim.id,
        paid_amount=Decimal("1000.00"),
        payment_date="20260620",
    )
    payment.claim_control_number = "FAC-PAID-1"
    db_session.commit()
    expectation = _create_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        patient_pos_id=pos.id,
        authorization_reference="FAC-PAID-1",
    )

    candidates = facility_payment_service.find_candidate_matches(db_session, expectation=expectation)
    facility_payment_service.confirm_allocation(
        db_session,
        allocation_id=candidates[0].id,
        user_id=TEST_USER_ID,
        user_role="BILLING",
    )
    db_session.refresh(expectation)
    rollup = facility_payment_service.compute_rollup(db_session, expectation)
    assert payment is not None
    assert expectation.reconciliation_status == "PAID"
    assert expectation.status == "PAID"
    assert rollup.confirmed_amount == Decimal("1000.00")


def test_partial_payment_marks_partially_paid(db_session, billing_enabled_tenant):
    cycle = _make_billing_cycle(db_session, billing_enabled_tenant, month=7)
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FVP6")
    pos = _make_patient_pos(db_session, billing_enabled_tenant, patient.id, pos_type="SNF", facility_name="Partial SNF", effective_date=date(2026, 7, 1))
    claim = _make_claim(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medi-Cal",
        total_charge=Decimal("500.00"),
        exported_days_ago=1,
    )
    remittance = _make_remittance(db_session, billing_enabled_tenant, payer_name="Medi-Cal", payment_date="20260710")
    _make_payment(
        db_session,
        tenant_id=billing_enabled_tenant,
        remittance_advice_id=remittance.id,
        claim_id=claim.id,
        paid_amount=Decimal("250.00"),
        payment_date="20260710",
    )
    expectation = _create_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        patient_pos_id=pos.id,
        expected_amount="500.00",
    )
    candidates = facility_payment_service.find_candidate_matches(db_session, expectation=expectation)
    facility_payment_service.confirm_allocation(db_session, allocation_id=candidates[0].id, user_id=TEST_USER_ID, user_role="BILLING")
    db_session.refresh(expectation)
    assert expectation.reconciliation_status == "PARTIALLY_PAID"
    assert expectation.status == "PARTIALLY_PAID"


def test_missing_payment_aging_uses_due_date_then_service_period_plus_30(db_session, billing_enabled_tenant):
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FVP7")
    pos = _make_patient_pos(db_session, billing_enabled_tenant, patient.id, pos_type="SNF", facility_name="Aging SNF", effective_date=date.today() - timedelta(days=120))
    expectation_due = _create_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        patient_pos_id=pos.id,
        due_date=date.today() - timedelta(days=95),
        service_period_start=date.today() - timedelta(days=150),
        service_period_end=date.today() - timedelta(days=121),
    )
    expectation_term = _create_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        patient_pos_id=pos.id,
        due_date=None,
        service_period_start=date.today() - timedelta(days=70),
        service_period_end=date.today() - timedelta(days=45),
    )
    aging_due = facility_payment_service.compute_aging(expectation_due)
    aging_term = facility_payment_service.compute_aging(expectation_term)
    assert aging_due["aging_bucket"] == "91-120"
    assert aging_term["aging_bucket"] == "0-30"
    assert aging_term["aging_basis_source"] == "SYSTEM_FALLBACK"


def test_overpayment_marks_overpaid(db_session, billing_enabled_tenant):
    cycle = _make_billing_cycle(db_session, billing_enabled_tenant, month=8)
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FVP8")
    pos = _make_patient_pos(db_session, billing_enabled_tenant, patient.id, pos_type="SNF", facility_name="Overpay SNF", effective_date=date(2026, 8, 1))
    claim = _make_claim(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medi-Cal",
        total_charge=Decimal("1100.00"),
        exported_days_ago=1,
    )
    remittance = _make_remittance(db_session, billing_enabled_tenant, payer_name="Medi-Cal", payment_date="20260810")
    _make_payment(
        db_session,
        tenant_id=billing_enabled_tenant,
        remittance_advice_id=remittance.id,
        claim_id=claim.id,
        paid_amount=Decimal("1100.10"),
        payment_date="20260810",
    )
    expectation = _create_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        patient_pos_id=pos.id,
        expected_amount="1100.00",
    )
    candidates = facility_payment_service.find_candidate_matches(db_session, expectation=expectation)
    facility_payment_service.confirm_allocation(db_session, allocation_id=candidates[0].id, user_id=TEST_USER_ID, user_role="BILLING")
    db_session.refresh(expectation)
    assert expectation.reconciliation_status == "OVERPAID"
    assert expectation.status == "OVERPAID"


def test_reversing_confirmed_allocation_recomputes_status(db_session, billing_enabled_tenant):
    cycle = _make_billing_cycle(db_session, billing_enabled_tenant, month=9)
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FVP9")
    pos = _make_patient_pos(db_session, billing_enabled_tenant, patient.id, pos_type="SNF", facility_name="Reverse SNF", effective_date=date(2026, 9, 1))
    claim = _make_claim(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medi-Cal",
        total_charge=Decimal("700.00"),
        exported_days_ago=1,
    )
    remittance = _make_remittance(db_session, billing_enabled_tenant, payer_name="Medi-Cal", payment_date="20260910")
    _make_payment(
        db_session,
        tenant_id=billing_enabled_tenant,
        remittance_advice_id=remittance.id,
        claim_id=claim.id,
        paid_amount=Decimal("700.00"),
        payment_date="20260910",
    )
    expectation = _create_expectation(db_session, tenant_id=billing_enabled_tenant, patient_id=patient.id, patient_pos_id=pos.id, expected_amount="700.00")
    candidates = facility_payment_service.find_candidate_matches(db_session, expectation=expectation)
    allocation = facility_payment_service.confirm_allocation(db_session, allocation_id=candidates[0].id, user_id=TEST_USER_ID, user_role="BILLING")
    reversed_allocation = facility_payment_service.reverse_allocation(
        db_session,
        allocation_id=allocation.id,
        user_id=TEST_USER_ID,
        reason="Posted to the wrong responsibility category.",
        user_role="BILLING",
    )
    db_session.refresh(expectation)
    assert reversed_allocation.allocation_status == "REVERSED"
    assert expectation.reconciliation_status == "EXPECTED"
    assert expectation.status == "ACTIVE"


def test_unmatched_candidate_creates_manual_review_allocation(db_session, billing_enabled_tenant):
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FV10")
    pos = _make_patient_pos(db_session, billing_enabled_tenant, patient.id, pos_type="SNF", facility_name="Manual SNF", effective_date=date(2026, 10, 1))
    remittance = _make_remittance(db_session, billing_enabled_tenant, payer_name="Random Payer", payment_date="20261015")
    _make_unmatched_payment(db_session, tenant_id=billing_enabled_tenant, remittance_advice_id=remittance.id, paid_amount="200.00")
    expectation = _create_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        patient_pos_id=pos.id,
        expected_amount="500.00",
        expected_payer_name_snapshot="Medi-Cal",
    )
    candidates = facility_payment_service.find_candidate_matches(db_session, expectation=expectation)
    assert len(candidates) == 1
    assert candidates[0].allocation_status == "MANUAL_REVIEW_REQUIRED"
    assert candidates[0].match_basis == "MANUAL_RECONCILIATION"


def test_wrong_patient_payment_never_appears_as_candidate(db_session, billing_enabled_tenant):
    cycle = _make_billing_cycle(db_session, billing_enabled_tenant, month=10)
    patient1 = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FV11A")
    patient2 = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FV11B")
    pos = _make_patient_pos(db_session, billing_enabled_tenant, patient1.id, pos_type="SNF", facility_name="Secure SNF", effective_date=date(2026, 10, 1))
    claim = _make_claim(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient2.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medi-Cal",
        total_charge=Decimal("500.00"),
        exported_days_ago=1,
    )
    remittance = _make_remittance(db_session, billing_enabled_tenant, payer_name="Medi-Cal", payment_date="20261010")
    payment = _make_payment(
        db_session,
        tenant_id=billing_enabled_tenant,
        remittance_advice_id=remittance.id,
        claim_id=claim.id,
        paid_amount=Decimal("500.00"),
        payment_date="20261010",
    )
    expectation = _create_expectation(db_session, tenant_id=billing_enabled_tenant, patient_id=patient1.id, patient_pos_id=pos.id, expected_amount="500.00")
    candidates = facility_payment_service.find_candidate_matches(db_session, expectation=expectation)
    assert all(candidate.payment_id != payment.id for candidate in candidates if candidate.payment_id is not None)


def test_duplicate_payment_cannot_be_double_confirmed(db_session, billing_enabled_tenant):
    cycle = _make_billing_cycle(db_session, billing_enabled_tenant, month=11)
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FV12")
    pos = _make_patient_pos(db_session, billing_enabled_tenant, patient.id, pos_type="SNF", facility_name="Duplicate SNF", effective_date=date(2026, 11, 1))
    claim = _make_claim(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medi-Cal",
        total_charge=Decimal("300.00"),
        exported_days_ago=1,
    )
    claim.claim_control_number = "DUP-001"
    db_session.commit()
    remittance = _make_remittance(db_session, billing_enabled_tenant, payer_name="Medi-Cal", payment_date="20261115")
    payment = _make_payment(
        db_session,
        tenant_id=billing_enabled_tenant,
        remittance_advice_id=remittance.id,
        claim_id=claim.id,
        paid_amount=Decimal("300.00"),
        payment_date="20261115",
    )
    payment.claim_control_number = "DUP-001"
    db_session.commit()
    expectation1 = _create_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        patient_pos_id=pos.id,
        expected_amount="300.00",
        authorization_reference="DUP-001",
    )
    expectation2 = _create_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        patient_pos_id=pos.id,
        responsibility_category="BOARD_AND_LODGING",
        expected_amount="300.00",
        authorization_reference="DUP-001",
    )
    first_candidate = facility_payment_service.find_candidate_matches(db_session, expectation=expectation1)[0]
    second_candidate = facility_payment_service.find_candidate_matches(db_session, expectation=expectation2)[0]
    facility_payment_service.confirm_allocation(db_session, allocation_id=first_candidate.id, user_id=TEST_USER_ID, user_role="BILLING")
    with pytest.raises(HTTPException) as exc:  # type: ignore[name-defined]
        facility_payment_service.confirm_allocation(db_session, allocation_id=second_candidate.id, user_id=TEST_USER_ID, user_role="BILLING")
    assert exc.value.status_code == 409
    assert payment.id is not None


def test_tenant_isolation_for_detail_and_list(client, db_session, billing_enabled_tenant):
    other_tenant_id = _make_second_tenant(db_session, legal_name="Other Facility Tenant")
    patient = _make_patient(db_session, other_tenant_id, mrn_prefix="FV13")
    pos = _make_patient_pos(db_session, other_tenant_id, patient.id, pos_type="SNF", facility_name="Isolated SNF", effective_date=date(2026, 12, 1))
    expectation = _create_expectation(db_session, tenant_id=other_tenant_id, patient_id=patient.id, patient_pos_id=pos.id)
    headers = _headers("CEO", billing_enabled_tenant)

    detail = client.get(f"/billing/facility-payments/expectations/{expectation.id}", headers=headers)
    listing = client.get("/billing/facility-payments/expectations", headers=headers)

    assert detail.status_code == 404
    assert listing.status_code == 200
    assert all(item["tenant_id"] == str(billing_enabled_tenant) for item in listing.json()["items"])


def test_overdue_90_alert_default_and_custom_thresholds(db_session, billing_enabled_tenant):
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FV14")
    pos = _make_patient_pos(db_session, billing_enabled_tenant, patient.id, pos_type="SNF", facility_name="Alert SNF", effective_date=date.today() - timedelta(days=140))
    expectation = _create_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        patient_pos_id=pos.id,
        due_date=date.today() - timedelta(days=95),
        service_period_start=date.today() - timedelta(days=130),
        service_period_end=date.today() - timedelta(days=100),
    )
    alerts = facility_payment_service.evaluate_alerts_for_expectation(db_session, expectation=expectation, user_id=TEST_USER_ID, user_role="BILLING")
    assert any(alert.alert_type == "OVERDUE_90" for alert in alerts)

    facility_payment_service.update_threshold(
        db_session,
        tenant_id=billing_enabled_tenant,
        alert_type="OVERDUE_90",
        enabled=True,
        threshold_amount=None,
        threshold_days=120,
        user_id=TEST_USER_ID,
        user_role="FINANCIAL_ADMIN",
    )
    patient2 = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FV14B")
    pos2 = _make_patient_pos(db_session, billing_enabled_tenant, patient2.id, pos_type="SNF", facility_name="Alert SNF 2", effective_date=date.today() - timedelta(days=120))
    expectation2 = _create_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient2.id,
        patient_pos_id=pos2.id,
        due_date=date.today() - timedelta(days=95),
        service_period_start=date.today() - timedelta(days=130),
        service_period_end=date.today() - timedelta(days=100),
    )
    alerts2 = facility_payment_service.evaluate_alerts_for_expectation(db_session, expectation=expectation2, user_id=TEST_USER_ID, user_role="BILLING")
    assert all(alert.alert_type != "OVERDUE_90" for alert in alerts2)


def test_alert_resolution_requires_evidence(client, db_session, billing_enabled_tenant):
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FV15")
    pos = _make_patient_pos(db_session, billing_enabled_tenant, patient.id, pos_type="SNF", facility_name="Resolve SNF", effective_date=date.today() - timedelta(days=140))
    expectation = _create_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        patient_pos_id=pos.id,
        due_date=date.today() - timedelta(days=95),
        service_period_start=date.today() - timedelta(days=130),
        service_period_end=date.today() - timedelta(days=100),
    )
    alerts = facility_payment_service.evaluate_alerts_for_expectation(db_session, expectation=expectation, user_id=TEST_USER_ID, user_role="BILLING")
    overdue_alert = next(alert for alert in alerts if alert.alert_type == "OVERDUE_90")
    headers = _headers("BILLING", billing_enabled_tenant)

    bad = client.post(
        f"/billing/facility-payments/alerts/{overdue_alert.id}/resolve",
        json={"resolution_evidence": ""},
        headers=headers,
    )
    good = client.post(
        f"/billing/facility-payments/alerts/{overdue_alert.id}/resolve",
        json={"resolution_evidence": "Confirmed EFT arrived and posted."},
        headers=headers,
    )

    assert bad.status_code == 400
    assert good.status_code == 200
    assert good.json()["status"] == "RESOLVED"


def test_decimal_precision_is_exact(db_session, billing_enabled_tenant):
    cycle = _make_billing_cycle(db_session, billing_enabled_tenant, month=1, year=2027)
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FV16")
    pos = _make_patient_pos(db_session, billing_enabled_tenant, patient.id, pos_type="SNF", facility_name="Decimal SNF", effective_date=date(2027, 1, 1))
    claim = _make_claim(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medi-Cal",
        total_charge=Decimal("0.30"),
        exported_days_ago=1,
    )
    remittance = _make_remittance(db_session, billing_enabled_tenant, payer_name="Medi-Cal", payment_date="20270110")
    _make_payment(db_session, tenant_id=billing_enabled_tenant, remittance_advice_id=remittance.id, claim_id=claim.id, paid_amount=Decimal("0.10"), payment_date="20270110")
    expectation = _create_expectation(db_session, tenant_id=billing_enabled_tenant, patient_id=patient.id, patient_pos_id=pos.id, expected_amount="0.30")
    candidate = facility_payment_service.find_candidate_matches(db_session, expectation=expectation)[0]
    facility_payment_service.confirm_allocation(db_session, allocation_id=candidate.id, user_id=TEST_USER_ID, user_role="BILLING")
    rollup = facility_payment_service.compute_rollup(db_session, expectation)
    assert rollup.confirmed_amount == Decimal("0.10")
    assert rollup.outstanding_amount == Decimal("0.20")


def test_correction_versioning_preserves_old_snapshot_and_writes_audit(db_session, billing_enabled_tenant):
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FV17")
    pos1 = _make_patient_pos(
        db_session,
        billing_enabled_tenant,
        patient.id,
        pos_type="SNF",
        facility_name="Original SNF",
        room_number="100A",
        effective_date=date(2026, 1, 1),
    )
    expectation = _create_expectation(db_session, tenant_id=billing_enabled_tenant, patient_id=patient.id, patient_pos_id=pos1.id)
    pos2 = _make_patient_pos(
        db_session,
        billing_enabled_tenant,
        patient.id,
        pos_type="ALF",
        facility_name="Corrected ALF",
        room_number="204",
        effective_date=date(2026, 2, 1),
    )
    corrected = facility_payment_service.create_corrected_expectation_version(
        db_session,
        previous_expectation_id=expectation.id,
        patient_pos_id=pos2.id,
        expected_amount=Decimal("1200.00"),
        correction_reason="Residence period corrected after intake review.",
        user_id=TEST_USER_ID,
        user_role="BILLING",
    )
    db_session.refresh(expectation)
    assert expectation.status == "SUPERSEDED"
    assert expectation.facility_name_snapshot == "Original SNF"
    assert corrected.facility_name_snapshot == "Corrected ALF"
    assert corrected.supersedes_expectation_id == expectation.id
    assert expectation.superseded_by_expectation_id == corrected.id
    assert corrected.version_number == expectation.version_number + 1
    audit_rows = db_session.query(FacilityPaymentAuditLog).filter(FacilityPaymentAuditLog.correlation_id.isnot(None)).all()
    assert audit_rows


def test_create_endpoint_defaults_to_draft_and_manual_due_date_source(client, db_session, billing_enabled_tenant):
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FVP19")
    pos = _make_patient_pos(
        db_session,
        billing_enabled_tenant,
        patient.id,
        pos_type="SNF",
        facility_name="Draft SNF",
        effective_date=date(2026, 4, 1),
    )
    response = client.post(
        f"/billing/facility-payments/expectations?tenant_id={billing_enabled_tenant}",
        json={
            "patient_id": str(patient.id),
            "patient_pos_id": str(pos.id),
            "responsibility_category": "ROOM_AND_BOARD",
            "expected_funding_source": "MEDICAID_FFS",
            "expected_amount": "875.50",
            "service_period_start": "2026-04-01",
            "service_period_end": "2026-04-30",
            "due_date": "2026-05-15",
            "source": "AUTHORIZED_MANUAL_ENTRY",
        },
        headers=_headers("BILLING", billing_enabled_tenant),
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "DRAFT"
    assert payload["row_version"] == 1
    assert payload["due_date_source"] == "AUTHORIZED_MANUAL_ENTRY"
    assert payload["payment_term_verified"] is True


def test_create_endpoint_rejects_protected_fields(client, db_session, billing_enabled_tenant):
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FVP20")
    response = client.post(
        f"/billing/facility-payments/expectations?tenant_id={billing_enabled_tenant}",
        json={
            "patient_id": str(patient.id),
            "responsibility_category": "ROOM_AND_BOARD",
            "expected_funding_source": "MEDICAID_FFS",
            "expected_amount": "100.00",
            "service_period_start": "2026-05-01",
            "service_period_end": "2026-05-31",
            "status": "ACTIVE",
        },
        headers=_headers("BILLING", billing_enabled_tenant),
    )
    assert response.status_code == 422


def test_activate_expectation_requires_complete_verified_source(client, db_session, billing_enabled_tenant):
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FVP21")
    draft = facility_payment_service.create_facility_payment_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        responsibility_category="ROOM_AND_BOARD",
        expected_funding_source="MEDICAID_FFS",
        expected_amount=Decimal("100.00"),
        service_period_start=date(2026, 6, 1),
        service_period_end=date(2026, 6, 30),
        source="NOT_VERIFIED",
        user_id=TEST_USER_ID,
        user_role="BILLING",
    )
    response = client.post(
        f"/billing/facility-payments/expectations/{draft.id}/activate",
        json={"expected_row_version": draft.row_version},
        headers=_headers("BILLING", billing_enabled_tenant),
    )
    assert response.status_code == 400
    assert "source" in response.text


def test_activate_expectation_promotes_draft_and_writes_audit(client, db_session, billing_enabled_tenant):
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FVP22")
    draft = facility_payment_service.create_facility_payment_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        responsibility_category="ROOM_AND_BOARD",
        expected_funding_source="MEDICAID_FFS",
        expected_amount=Decimal("250.00"),
        service_period_start=date(2026, 7, 1),
        service_period_end=date(2026, 7, 31),
        source="AUTHORIZED_MANUAL_ENTRY",
        user_id=TEST_USER_ID,
        user_role="BILLING",
    )
    response = client.post(
        f"/billing/facility-payments/expectations/{draft.id}/activate",
        json={"expected_row_version": draft.row_version},
        headers=_headers("BILLING", billing_enabled_tenant),
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "ACTIVE"
    assert payload["row_version"] == 2
    audit = (
        db_session.query(FacilityPaymentAuditLog)
        .filter(
            FacilityPaymentAuditLog.entity_id == draft.id,
            FacilityPaymentAuditLog.field_name == "EXPECTATION_ACTIVATED",
        )
        .one_or_none()
    )
    assert audit is not None


def test_correction_conflict_and_allocation_review_flags(client, db_session, billing_enabled_tenant):
    cycle = _make_billing_cycle(db_session, billing_enabled_tenant, month=8)
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FVP23")
    pos = _make_patient_pos(db_session, billing_enabled_tenant, patient.id, pos_type="SNF", facility_name="Flag SNF", effective_date=date(2026, 8, 1))
    claim = _make_claim(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medi-Cal",
        total_charge=Decimal("500.00"),
        exported_days_ago=1,
    )
    remittance = _make_remittance(db_session, billing_enabled_tenant, payer_name="Medi-Cal", payment_date="20260810")
    _make_payment(
        db_session,
        tenant_id=billing_enabled_tenant,
        remittance_advice_id=remittance.id,
        claim_id=claim.id,
        paid_amount=Decimal("500.00"),
        payment_date="20260810",
    )
    expectation = _create_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        patient_pos_id=pos.id,
        expected_amount="500.00",
    )
    allocation = facility_payment_service.find_candidate_matches(db_session, expectation=expectation)[0]
    facility_payment_service.confirm_allocation(
        db_session, allocation_id=allocation.id, user_id=TEST_USER_ID, user_role="BILLING"
    )
    stale = client.post(
        f"/billing/facility-payments/expectations/{expectation.id}/correct",
        json={"expected_amount": "600.00", "correction_reason": "Raise amount.", "expected_row_version": 0},
        headers=_headers("BILLING", billing_enabled_tenant),
    )
    assert stale.status_code == 409

    good = client.post(
        f"/billing/facility-payments/expectations/{expectation.id}/correct",
        json={
            "expected_amount": "600.00",
            "service_period_end": "2026-08-30",
            "correction_reason": "Adjusted service month.",
            "expected_row_version": expectation.row_version,
        },
        headers=_headers("BILLING", billing_enabled_tenant),
    )
    assert good.status_code == 200, good.text
    db_session.expire_all()
    flagged = db_session.get(FacilityPaymentAllocation, allocation.id)
    assert flagged is not None
    assert flagged.flagged_for_review is True
    assert flagged.flagged_reason is not None


def test_cancellation_requires_reason_and_force_when_confirmed_allocations(client, db_session, billing_enabled_tenant):
    cycle = _make_billing_cycle(db_session, billing_enabled_tenant, month=9)
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FVP24")
    pos = _make_patient_pos(db_session, billing_enabled_tenant, patient.id, pos_type="SNF", facility_name="Cancel SNF", effective_date=date(2026, 9, 1))
    claim = _make_claim(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medi-Cal",
        total_charge=Decimal("400.00"),
        exported_days_ago=1,
    )
    remittance = _make_remittance(db_session, billing_enabled_tenant, payer_name="Medi-Cal", payment_date="20260915")
    _make_payment(
        db_session,
        tenant_id=billing_enabled_tenant,
        remittance_advice_id=remittance.id,
        claim_id=claim.id,
        paid_amount=Decimal("400.00"),
        payment_date="20260915",
    )
    expectation = _create_expectation(db_session, tenant_id=billing_enabled_tenant, patient_id=patient.id, patient_pos_id=pos.id, expected_amount="400.00")
    allocation = facility_payment_service.find_candidate_matches(db_session, expectation=expectation)[0]
    facility_payment_service.confirm_allocation(db_session, allocation_id=allocation.id, user_id=TEST_USER_ID, user_role="BILLING")

    missing_reason = client.post(
        f"/billing/facility-payments/expectations/{expectation.id}/cancel",
        json={"cancellation_reason": "", "expected_row_version": expectation.row_version},
        headers=_headers("BILLING", billing_enabled_tenant),
    )
    blocked = client.post(
        f"/billing/facility-payments/expectations/{expectation.id}/cancel",
        json={"cancellation_reason": "Void expectation", "expected_row_version": expectation.row_version},
        headers=_headers("BILLING", billing_enabled_tenant),
    )
    forced = client.post(
        f"/billing/facility-payments/expectations/{expectation.id}/cancel",
        json={"cancellation_reason": "Void expectation", "force": True, "expected_row_version": expectation.row_version},
        headers=_headers("BILLING", billing_enabled_tenant),
    )

    assert missing_reason.status_code == 400
    assert blocked.status_code == 409
    assert forced.status_code == 200, forced.text
    payload = forced.json()
    assert payload["status"] == "CANCELLED"
    assert payload["cancelled_by"] == str(TEST_USER_ID)
    db_session.expire_all()
    flagged = db_session.get(FacilityPaymentAllocation, allocation.id)
    assert flagged is not None
    assert flagged.flagged_for_review is True


def test_residence_snapshot_diff_and_history_endpoints(client, db_session, billing_enabled_tenant):
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FVP25")
    pos1 = _make_patient_pos(db_session, billing_enabled_tenant, patient.id, pos_type="SNF", facility_name="History SNF", effective_date=date(2026, 10, 1))
    expectation = _create_expectation(db_session, tenant_id=billing_enabled_tenant, patient_id=patient.id, patient_pos_id=pos1.id)
    pos2 = _make_patient_pos(db_session, billing_enabled_tenant, patient.id, pos_type="ALF", facility_name="History ALF", effective_date=date(2026, 10, 15))
    corrected = facility_payment_service.create_corrected_expectation_version(
        db_session,
        previous_expectation_id=expectation.id,
        patient_pos_id=pos2.id,
        correction_reason="Residence changed.",
        user_id=TEST_USER_ID,
        user_role="BILLING",
        expected_row_version=expectation.row_version,
    )

    history_response = client.get(
        f"/billing/facility-payments/expectations/{corrected.id}/history",
        headers=_headers("BILLING", billing_enabled_tenant),
    )
    diff_response = client.get(
        f"/billing/facility-payments/expectations/{expectation.id}/residence-snapshot-diff",
        headers=_headers("BILLING", billing_enabled_tenant),
    )

    assert history_response.status_code == 200
    assert [item["version_number"] for item in history_response.json()["items"]] == [1, 2]
    assert diff_response.status_code == 200
    assert diff_response.json()["has_changes"] is True


def test_create_expectation_idempotency_returns_existing_row(db_session, billing_enabled_tenant):
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FVP26")
    request_id = uuid.uuid4()
    first = _create_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        client_request_id=request_id,
        due_date=None,
        status="DRAFT",
        source="NOT_VERIFIED",
    )
    second = facility_payment_service.create_facility_payment_expectation(
        db_session,
        tenant_id=billing_enabled_tenant,
        patient_id=patient.id,
        responsibility_category="ROOM_AND_BOARD",
        expected_funding_source="MEDICAID_FFS",
        expected_amount=Decimal("1000.00"),
        service_period_start=date(2026, 3, 1),
        service_period_end=date(2026, 3, 31),
        client_request_id=request_id,
        user_id=TEST_USER_ID,
        user_role="BILLING",
    )
    assert first.id == second.id
    assert first.due_date_source == "SYSTEM_FALLBACK"
    assert first.payment_term_verified is False


def test_collections_report_empty_state(client, db_session, billing_enabled_tenant):
    headers = _headers("BILLING", billing_enabled_tenant)
    response = client.get("/billing/facility-payments/collections-report", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["rows"] == []
    assert payload["summary"]["total_expected"] == "0.00"


def test_router_end_to_end_create_list_thresholds(client, db_session, billing_enabled_tenant):
    patient = _make_patient(db_session, billing_enabled_tenant, mrn_prefix="FV18")
    pos = _make_patient_pos(db_session, billing_enabled_tenant, patient.id, pos_type="SNF", facility_name="Router SNF", effective_date=date(2026, 3, 1))
    headers = _headers("BILLING", billing_enabled_tenant)

    create_response = client.post(
        "/billing/facility-payments/expectations",
        json={
            "patient_id": str(patient.id),
            "patient_pos_id": str(pos.id),
            "responsibility_category": "ROOM_AND_BOARD",
            "expected_funding_source": "MEDICAID_FFS",
            "expected_amount": "875.50",
            "service_period_start": "2026-03-01",
            "service_period_end": "2026-03-31",
            "due_date": "2026-04-15",
            "expected_payer_name_snapshot": "Medi-Cal",
        },
        headers=headers,
    )
    list_response = client.get("/billing/facility-payments/expectations", headers=headers)
    thresholds_response = client.get("/billing/facility-payments/alert-thresholds", headers=headers)

    assert create_response.status_code == 200
    assert list_response.status_code == 200
    assert list_response.json()["count"] >= 1
    assert thresholds_response.status_code == 200
    assert any(item["alert_type"] == "OVERDUE_90" for item in thresholds_response.json()["items"])
