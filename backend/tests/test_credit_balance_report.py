from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.billing.models.credit_balance_case import CreditBalanceCase
from app.billing.services.credit_balance_case_service import (
    CLOSE_CASE,
    CONFIRM_CREDIT,
    DETERMINE_REPAYMENT_REQUIRED,
    INITIATE_REFUND,
    RECORD_REFUND,
    REJECT_CREDIT,
    REQUEST_INVESTIGATION,
    open_case_for_claim,
    perform_action,
)
from app.billing.services.credit_balance_service import (
    MEDICARE_REPORTABLE,
    UNKNOWN,
    build_credit_balance_report,
    classify_medicare_reportability,
)
from app.models.patient_payer import PatientPayer

from tests.test_aging_report_service import (
    _enable_billing_for_tenant,
    _headers,
    _make_adjustment,
    _make_billing_cycle,
    _make_claim,
    _make_patient,
    _make_payment,
    _make_remittance,
    _make_written_off_denial,
)


def _make_payer(db_session, patient, payer_name: str, payer_type: str) -> PatientPayer:
    payer = PatientPayer(
        id=uuid.uuid4(),
        patient_id=patient.id,
        payer_name=payer_name,
        payer_type=payer_type,
        is_primary=True,
        effective_start_date=date(2020, 1, 1),
    )
    db_session.add(payer)
    db_session.commit()
    return payer


# ---------------------------------------------------------------------
# Medicare CMS-838 classification -- driven by real PatientPayer.payer_type
# metadata (see app.billing.services.msp_validation_service.
# MEDICARE_PAYER_TYPES), never guessed from the payer name string.
# ---------------------------------------------------------------------
def test_classify_medicare_reportability_medicare_payer_type():
    assert classify_medicare_reportability("MEDICARE") == MEDICARE_REPORTABLE
    assert classify_medicare_reportability("medicare_hospice") == MEDICARE_REPORTABLE


def test_classify_medicare_reportability_non_medicare_payer_type():
    assert classify_medicare_reportability("MEDICAID") == "NON_MEDICARE"
    assert classify_medicare_reportability("COMMERCIAL") == "NON_MEDICARE"
    assert classify_medicare_reportability("WORKERS_COMP") == "NON_MEDICARE"


def test_classify_medicare_reportability_missing_payer_type_unknown():
    assert classify_medicare_reportability(None) == UNKNOWN
    assert classify_medicare_reportability("") == UNKNOWN
    assert classify_medicare_reportability("   ") == UNKNOWN


def test_classify_medicare_reportability_never_infers_from_payer_name():
    """
    A payer_type value of "MEDICARE_ADVANTAGE" doesn't exist anywhere in
    this schema (see app.billing.services.msp_validation_service.
    MEDICARE_PAYER_TYPES) -- confirming the classifier only trusts real
    payer_type values and does not fall back to parsing payer names for
    concepts the system has no structured way to represent.
    """
    assert classify_medicare_reportability("SOME_UNRECOGNIZED_TYPE") == "NON_MEDICARE"


def test_report_credit_item_uses_patient_payer_metadata_for_classification(db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Payer Metadata Agency")
    cycle = _make_billing_cycle(db_session, tenant_id, month=6)

    patient = _make_patient(db_session, tenant_id, mrn_prefix="PMD1")
    _make_payer(db_session, patient, "Medicare", "MEDICARE")
    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("100.00"),
        exported_days_ago=1,
    )
    ra = _make_remittance(db_session, tenant_id)
    _make_payment(db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim.id, paid_amount=Decimal("150.00"))

    report = build_credit_balance_report(db_session, [tenant_id])
    item = report["claim_credit_items"][0]
    assert item["medicare_classification"] == MEDICARE_REPORTABLE
    assert item["data_completeness"] == "COMPLETE"


def test_report_surfaces_primary_and_secondary_payer_from_priority_order(db_session, tenant):
    """
    Hospice-typical coordination-of-benefits: Medicare Hospice primary,
    Medi-Cal secondary. Primary/secondary payer NAMES are billing context
    surfaced from existing PatientPayer.priority_order -- this must never
    collapse/replace the claim's own billed payer_name.
    """
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="COB Agency")
    cycle = _make_billing_cycle(db_session, tenant_id, month=9)

    patient = _make_patient(db_session, tenant_id, mrn_prefix="COB1")
    primary = _make_payer(db_session, patient, "Medicare Hospice", "MEDICARE_HOSPICE")
    primary.priority_order = 1
    secondary = _make_payer(db_session, patient, "Medi-Cal", "MEDICAID")
    secondary.priority_order = 2
    db_session.commit()

    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare Hospice",
        total_charge=Decimal("100.00"),
        exported_days_ago=1,
    )
    ra = _make_remittance(db_session, tenant_id, payer_name="Medicare Hospice", payment_date="20260315")
    _make_payment(
        db_session,
        tenant_id=tenant_id,
        remittance_advice_id=ra.id,
        claim_id=claim.id,
        paid_amount=Decimal("150.00"),
        payment_date="20260315",
    )

    report = build_credit_balance_report(db_session, [tenant_id])
    item = report["claim_credit_items"][0]
    assert item["payer_name"] == "Medicare Hospice"
    assert item["primary_payer_name"] == "Medicare Hospice"
    assert item["secondary_payer_name"] == "Medi-Cal"
    assert item["primary_payer_paid"]["amount"] == "150.00"
    assert item["secondary_payer_paid"]["amount"] == "0.00"
    assert item["most_recent_payment_date"] == "20260315"

    account = report["patient_accounts"][0]
    assert account["primary_payer_name"] == "Medicare Hospice"
    assert account["secondary_payer_name"] == "Medi-Cal"


def test_report_credit_item_without_patient_payer_is_unknown(db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="No Payer Metadata Agency")
    cycle = _make_billing_cycle(db_session, tenant_id, month=7)

    patient = _make_patient(db_session, tenant_id, mrn_prefix="PMD2")
    # Intentionally no PatientPayer row -- classification must never be
    # guessed from the claim's payer_name string.
    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("100.00"),
        exported_days_ago=1,
    )
    ra = _make_remittance(db_session, tenant_id)
    _make_payment(db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim.id, paid_amount=Decimal("150.00"))

    report = build_credit_balance_report(db_session, [tenant_id])
    item = report["claim_credit_items"][0]
    assert item["medicare_classification"] == UNKNOWN
    assert item["data_completeness"] == "PARTIAL"


def test_report_flags_potential_duplicate_payment_without_assigning_reason(db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Dup Payment Agency")
    cycle = _make_billing_cycle(db_session, tenant_id, month=8)

    patient = _make_patient(db_session, tenant_id, mrn_prefix="DUP1")
    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("100.00"),
        exported_days_ago=1,
    )
    ra = _make_remittance(db_session, tenant_id)
    # Two payments with the exact same amount -- a mechanical duplicate
    # signal only; the system must never guess whether this is really a
    # duplicate payment, a posting error, COB, MSP, or recoupment timing.
    _make_payment(db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim.id, paid_amount=Decimal("80.00"))
    _make_payment(db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim.id, paid_amount=Decimal("80.00"))

    report = build_credit_balance_report(db_session, [tenant_id])
    item = report["claim_credit_items"][0]
    assert item["potential_duplicate_payment"] is True
    assert item["reason_code"] is None


def test_report_does_not_flag_single_payment_as_duplicate(db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="No Dup Payment Agency")
    cycle = _make_billing_cycle(db_session, tenant_id, month=9)

    patient = _make_patient(db_session, tenant_id, mrn_prefix="DUP2")
    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("100.00"),
        exported_days_ago=1,
    )
    ra = _make_remittance(db_session, tenant_id)
    _make_payment(db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim.id, paid_amount=Decimal("150.00"))

    report = build_credit_balance_report(db_session, [tenant_id])
    item = report["claim_credit_items"][0]
    assert item["potential_duplicate_payment"] is False


def test_perform_action_rejects_reason_code_outside_enumeration(client, db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Reason Code Agency")
    cycle = _make_billing_cycle(db_session, tenant_id, month=10)

    patient = _make_patient(db_session, tenant_id, mrn_prefix="RSC1")
    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("100.00"),
        exported_days_ago=1,
    )
    ra = _make_remittance(db_session, tenant_id)
    _make_payment(db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim.id, paid_amount=Decimal("150.00"))

    headers = _headers("BILLING", tenant_id)
    open_response = client.post("/billing/credit-balance/cases", headers=headers, json={"claim_id": str(claim.id)})
    case_id = open_response.json()["case_id"]

    bad_response = client.post(
        f"/billing/credit-balance/cases/{case_id}/actions",
        headers=headers,
        json={"action": "REQUEST_INVESTIGATION", "reason": "Reviewing possible duplicate.", "reason_code": "MADE_UP_CODE"},
    )
    assert bad_response.status_code == 400

    good_response = client.post(
        f"/billing/credit-balance/cases/{case_id}/actions",
        headers=headers,
        json={"action": "REQUEST_INVESTIGATION", "reason": "Reviewing possible duplicate.", "reason_code": "duplicate_payment"},
    )
    assert good_response.status_code == 200, good_response.text
    assert good_response.json()["reason_code"] == "DUPLICATE_PAYMENT"


def test_reason_codes_endpoint_returns_enumeration(client, db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    headers = _headers("BILLING", tenant_id)
    response = client.get("/billing/credit-balance/reason-codes", headers=headers)
    assert response.status_code == 200, response.text
    codes = response.json()["reason_codes"]
    assert "DUPLICATE_PAYMENT" in codes
    assert "POSTING_ERROR" in codes
    assert "COB_ISSUE" in codes
    assert "MSP_ISSUE" in codes
    assert "RECOUPMENT_TIMING" in codes
    assert "OTHER" in codes


# ---------------------------------------------------------------------
# Claim-level credit detection + patient-account summary
# ---------------------------------------------------------------------
def test_single_overpaid_claim_produces_claim_credit_item(db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Credit Balance Test Hospice")
    cycle = _make_billing_cycle(db_session, tenant_id, month=4)
    patient = _make_patient(db_session, tenant_id, mrn_prefix="CB1")
    _make_payer(db_session, patient, "Medicare", "MEDICARE")
    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("500.00"),
        exported_days_ago=10,
    )
    ra = _make_remittance(db_session, tenant_id)
    _make_payment(db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim.id, paid_amount=Decimal("700.00"))
    # 500 - 700 = -200 -> credit balance of 200.00

    report = build_credit_balance_report(db_session, [tenant_id])

    assert report["summary"]["claim_count"] == 1
    assert report["summary"]["total_potential_credits"]["amount"] == "200.00"
    item = report["claim_credit_items"][0]
    assert item["claim_id"] == str(claim.id)
    assert item["credit_amount"]["amount"] == "200.00"
    assert item["credit_amount"]["currency"] == "USD"
    assert item["medicare_classification"] == MEDICARE_REPORTABLE
    assert item["case_id"] is None
    assert item["case_status"] == "POTENTIAL"

    account = report["patient_accounts"][0]
    assert account["claims_with_credit"] == 1
    assert account["total_credit_balance"]["amount"] == "200.00"
    assert account["net_patient_account_balance"]["amount"] == "-200.00"


def test_fully_paid_claim_zero_balance_excluded(db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Zero Balance Hospice")
    cycle = _make_billing_cycle(db_session, tenant_id, month=4)
    patient = _make_patient(db_session, tenant_id, mrn_prefix="CB0")
    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("400.00"),
        exported_days_ago=10,
    )
    ra = _make_remittance(db_session, tenant_id)
    _make_payment(db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim.id, paid_amount=Decimal("400.00"))

    report = build_credit_balance_report(db_session, [tenant_id])
    assert report["summary"]["claim_count"] == 0
    assert report["claim_credit_items"] == []
    assert report["patient_accounts"] == []


def test_contractual_adjustment_produces_credit(db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Adjustment Hospice")
    cycle = _make_billing_cycle(db_session, tenant_id, month=4)
    patient = _make_patient(db_session, tenant_id, mrn_prefix="CB2")
    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Aetna",
        total_charge=Decimal("300.00"),
        exported_days_ago=5,
    )
    ra = _make_remittance(db_session, tenant_id)
    payment = _make_payment(db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim.id, paid_amount=Decimal("300.00"))
    _make_adjustment(db_session, payment_id=payment.id, group_code="CO", carc_code="45", amount=Decimal("50.00"))
    # 300 - 300 - 50 = -50 -> credit balance 50.00

    report = build_credit_balance_report(db_session, [tenant_id])
    assert report["summary"]["total_potential_credits"]["amount"] == "50.00"
    assert report["claim_credit_items"][0]["credit_amount"]["amount"] == "50.00"


def test_written_off_denial_produces_credit(db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Write Off Hospice")
    cycle = _make_billing_cycle(db_session, tenant_id, month=4)
    patient = _make_patient(db_session, tenant_id, mrn_prefix="CB3")
    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("600.00"),
        exported_days_ago=5,
    )
    ra = _make_remittance(db_session, tenant_id)
    _make_payment(db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim.id, paid_amount=Decimal("550.00"))
    _make_written_off_denial(db_session, tenant_id=tenant_id, claim_id=claim.id, amount=Decimal("100.00"))
    # 600 - 550 - 100 = -50 -> credit balance 50.00

    report = build_credit_balance_report(db_session, [tenant_id])
    assert report["claim_credit_items"][0]["credit_amount"]["amount"] == "50.00"


def test_multiple_payments_reversal_recoupment_nets_to_credit(db_session, tenant):
    """
    A negative-amount subsequent Payment row (representing a payer
    reversal/recoupment posted on a later 835) must net against the
    original payment when computing the claim balance.
    """
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Reversal Hospice")
    cycle = _make_billing_cycle(db_session, tenant_id, month=4)
    patient = _make_patient(db_session, tenant_id, mrn_prefix="CB4")
    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("500.00"),
        exported_days_ago=5,
    )
    ra = _make_remittance(db_session, tenant_id)
    # Original payment overpays by 100.
    _make_payment(db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim.id, paid_amount=Decimal("600.00"))
    # Payer partially recoups on a later 835 -- but not enough to erase the credit.
    _make_payment(db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim.id, paid_amount=Decimal("-50.00"))
    # net paid = 550, 500 - 550 = -50 -> credit balance 50.00

    report = build_credit_balance_report(db_session, [tenant_id])
    assert report["claim_credit_items"][0]["credit_amount"]["amount"] == "50.00"
    assert report["claim_credit_items"][0]["payment_count"] == 2


def test_patient_with_positive_ar_and_claim_level_credit_not_netted(db_session, tenant):
    """
    A patient with one overpaid claim (-1000) and one outstanding claim
    (+1000) nets to $0 at the patient level, but the claim-level credit
    must still be reported in full -- never suppressed by patient netting.
    """
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Net Zero Hospice")
    cycle = _make_billing_cycle(db_session, tenant_id, month=4)
    patient = _make_patient(db_session, tenant_id, mrn_prefix="CB5")

    claim_credit = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("1000.00"),
        exported_days_ago=5,
    )
    ra = _make_remittance(db_session, tenant_id)
    _make_payment(db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim_credit.id, paid_amount=Decimal("2000.00"))

    cycle2 = _make_billing_cycle(db_session, tenant_id, month=5)
    claim_outstanding = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle2.id,
        status="SENT",
        payer_name="Medicare",
        total_charge=Decimal("1000.00"),
        exported_days_ago=5,
    )
    # no payment -> fully outstanding, +1000

    report = build_credit_balance_report(db_session, [tenant_id])

    assert report["summary"]["claim_count"] == 1  # only the credit claim shows as a claim_credit_item
    credit_ids = {c["claim_id"] for c in report["claim_credit_items"]}
    assert str(claim_credit.id) in credit_ids
    assert str(claim_outstanding.id) not in credit_ids

    account = report["patient_accounts"][0]
    assert account["total_positive_ar"]["amount"] == "1000.00"
    assert account["total_credit_balance"]["amount"] == "1000.00"
    assert account["net_patient_account_balance"]["amount"] == "0.00"
    assert account["claims_with_credit"] == 1


def test_empty_scope_returns_empty_report(db_session):
    report = build_credit_balance_report(db_session, [])
    assert report["summary"]["claim_count"] == 0
    assert report["claim_credit_items"] == []
    assert report["patient_accounts"] == []


def test_report_generation_is_idempotent(db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Idempotent Hospice")
    cycle = _make_billing_cycle(db_session, tenant_id, month=4)
    patient = _make_patient(db_session, tenant_id, mrn_prefix="CB6")
    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("250.00"),
        exported_days_ago=5,
    )
    ra = _make_remittance(db_session, tenant_id)
    _make_payment(db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim.id, paid_amount=Decimal("300.00"))

    first = build_credit_balance_report(db_session, [tenant_id])
    second = build_credit_balance_report(db_session, [tenant_id])
    assert first["summary"] == second["summary"]
    assert first["claim_credit_items"] == second["claim_credit_items"]


def test_decimal_precision_no_floats_in_serialized_output(db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Decimal Hospice")
    cycle = _make_billing_cycle(db_session, tenant_id, month=4)
    patient = _make_patient(db_session, tenant_id, mrn_prefix="CB7")
    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("100.10"),
        exported_days_ago=5,
    )
    ra = _make_remittance(db_session, tenant_id)
    _make_payment(db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim.id, paid_amount=Decimal("100.13"))

    report = build_credit_balance_report(db_session, [tenant_id])
    amount_field = report["claim_credit_items"][0]["credit_amount"]["amount"]
    assert isinstance(amount_field, str)
    assert amount_field == "0.03"


# ---------------------------------------------------------------------
# Case lifecycle
# ---------------------------------------------------------------------
def test_open_case_is_idempotent(db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Idempotent Case Hospice")
    cycle = _make_billing_cycle(db_session, tenant_id, month=4)
    patient = _make_patient(db_session, tenant_id, mrn_prefix="CB8")
    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("100.00"),
        exported_days_ago=5,
    )

    case1 = open_case_for_claim(
        db_session,
        tenant_id=tenant_id,
        claim_id=claim.id,
        patient_id=patient.id,
        credit_amount=Decimal("50.00"),
        medicare_classification=MEDICARE_REPORTABLE,
        performed_by="tester@example.com",
    )
    case2 = open_case_for_claim(
        db_session,
        tenant_id=tenant_id,
        claim_id=claim.id,
        patient_id=patient.id,
        credit_amount=Decimal("50.00"),
        medicare_classification=MEDICARE_REPORTABLE,
        performed_by="tester@example.com",
    )
    assert case1.id == case2.id
    assert case1.status == "POTENTIAL"


def _make_case(db_session, tenant_id, claim, patient) -> CreditBalanceCase:
    return open_case_for_claim(
        db_session,
        tenant_id=tenant_id,
        claim_id=claim.id,
        patient_id=patient.id,
        credit_amount=Decimal("75.00"),
        medicare_classification=MEDICARE_REPORTABLE,
        performed_by="tester@example.com",
    )


def test_confirm_then_refund_lifecycle_transitions(db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Lifecycle Hospice")
    cycle = _make_billing_cycle(db_session, tenant_id, month=4)
    patient = _make_patient(db_session, tenant_id, mrn_prefix="CB9")
    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("100.00"),
        exported_days_ago=5,
    )
    case = _make_case(db_session, tenant_id, claim, patient)

    case = perform_action(db_session, case, REQUEST_INVESTIGATION, performed_by="biller1", reason="Looking into duplicate payment.")
    assert case.status == "UNDER_REVIEW"
    assert case.review_started_at is not None

    case = perform_action(db_session, case, CONFIRM_CREDIT, performed_by="biller1", reason="Confirmed duplicate ERA posting.")
    assert case.status == "CONFIRMED"
    assert case.confirmed_at is not None
    assert case.identified_at is not None

    case = perform_action(
        db_session,
        case,
        DETERMINE_REPAYMENT_REQUIRED,
        performed_by="biller1",
        reason="Repayment required per CMS 60-day rule.",
        repayment_due_at=date.today() + timedelta(days=60),
    )
    assert case.status == "REPAYMENT_REQUIRED"
    assert case.repayment_due_at is not None

    case = perform_action(db_session, case, INITIATE_REFUND, performed_by="biller1", reason="Refund check requested.")
    assert case.status == "REFUND_PENDING"

    case = perform_action(
        db_session,
        case,
        RECORD_REFUND,
        performed_by="biller1",
        reason="Refund check #1234 mailed to Medicare.",
        source_transaction_reference="check-1234",
        amount="75.00",
    )
    assert case.status == "RESOLVED_REPAID"
    assert case.amount_repaid == Decimal("75.00")
    assert case.repaid_at is not None

    case = perform_action(db_session, case, CLOSE_CASE, performed_by="biller1", reason="Case fully resolved.")
    assert case.status == "CLOSED"

    assert len(case.events) == 7  # CASE_OPENED + 6 recorded events across the 5 actions above


def test_reject_credit_transition(db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Reject Hospice")
    cycle = _make_billing_cycle(db_session, tenant_id, month=4)
    patient = _make_patient(db_session, tenant_id, mrn_prefix="CBA")
    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("100.00"),
        exported_days_ago=5,
    )
    case = _make_case(db_session, tenant_id, claim, patient)
    case = perform_action(db_session, case, REJECT_CREDIT, performed_by="biller1", reason="Calculation error -- payment was correctly matched.")
    assert case.status == "NOT_A_CREDIT_BALANCE"
    assert case.resolved_at is not None


def test_invalid_transition_is_rejected(db_session, tenant):
    from fastapi import HTTPException

    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Invalid Transition Hospice")
    cycle = _make_billing_cycle(db_session, tenant_id, month=4)
    patient = _make_patient(db_session, tenant_id, mrn_prefix="CBB")
    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("100.00"),
        exported_days_ago=5,
    )
    case = _make_case(db_session, tenant_id, claim, patient)

    try:
        perform_action(db_session, case, RECORD_REFUND, performed_by="biller1", reason="Should not be allowed yet.")
        assert False, "Expected HTTPException for invalid transition"
    except HTTPException as exc:
        assert exc.status_code == 409


def test_action_requires_a_reason(db_session, tenant):
    from fastapi import HTTPException

    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Reason Required Hospice")
    cycle = _make_billing_cycle(db_session, tenant_id, month=4)
    patient = _make_patient(db_session, tenant_id, mrn_prefix="CBC")
    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("100.00"),
        exported_days_ago=5,
    )
    case = _make_case(db_session, tenant_id, claim, patient)

    try:
        perform_action(db_session, case, REQUEST_INVESTIGATION, performed_by="biller1", reason="   ")
        assert False, "Expected HTTPException for missing reason"
    except HTTPException as exc:
        assert exc.status_code == 400


# ---------------------------------------------------------------------
# HTTP-level endpoint tests
# ---------------------------------------------------------------------
def test_credit_balance_report_endpoint(client, db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Endpoint Credit Hospice")
    cycle = _make_billing_cycle(db_session, tenant_id, month=4)
    patient = _make_patient(db_session, tenant_id, mrn_prefix="EPCB")
    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("100.00"),
        exported_days_ago=5,
    )
    ra = _make_remittance(db_session, tenant_id)
    _make_payment(db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim.id, paid_amount=Decimal("150.00"))

    response = client.get(
        "/billing/credit-balance/report",
        headers=_headers("BILLING", tenant_id),
        params={"tenant_id": str(tenant_id)},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["summary"]["claim_count"] == 1
    assert payload["claim_credit_items"][0]["credit_amount"]["amount"] == "50.00"


def test_open_case_and_act_via_http(client, db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="HTTP Case Hospice")
    cycle = _make_billing_cycle(db_session, tenant_id, month=4)
    patient = _make_patient(db_session, tenant_id, mrn_prefix="EPCC")
    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("100.00"),
        exported_days_ago=5,
    )
    ra = _make_remittance(db_session, tenant_id)
    _make_payment(db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim.id, paid_amount=Decimal("150.00"))

    headers = _headers("BILLING", tenant_id)

    create_response = client.post(
        "/billing/credit-balance/cases",
        headers=headers,
        json={"claim_id": str(claim.id)},
    )
    assert create_response.status_code == 200, create_response.text
    case_payload = create_response.json()
    assert case_payload["status"] == "POTENTIAL"
    case_id = case_payload["case_id"]

    action_response = client.post(
        f"/billing/credit-balance/cases/{case_id}/actions",
        headers=headers,
        json={"action": REQUEST_INVESTIGATION, "reason": "Reviewing duplicate ERA."},
    )
    assert action_response.status_code == 200, action_response.text
    assert action_response.json()["status"] == "UNDER_REVIEW"

    list_response = client.get(
        "/billing/credit-balance/cases",
        headers=headers,
        params={"tenant_id": str(tenant_id)},
    )
    assert list_response.status_code == 200
    assert len(list_response.json()["cases"]) == 1


def test_cms_838_export_only_includes_medicare_reportable(client, db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="CMS838 Hospice")
    cycle = _make_billing_cycle(db_session, tenant_id, month=4)

    patient_medicare = _make_patient(db_session, tenant_id, mrn_prefix="CBM1")
    _make_payer(db_session, patient_medicare, "Medicare", "MEDICARE")
    claim_medicare = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_medicare.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medicare",
        total_charge=Decimal("100.00"),
        exported_days_ago=5,
    )
    ra = _make_remittance(db_session, tenant_id)
    _make_payment(db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim_medicare.id, paid_amount=Decimal("150.00"))

    cycle2 = _make_billing_cycle(db_session, tenant_id, month=5)
    patient_aetna = _make_patient(db_session, tenant_id, mrn_prefix="CBM2")
    _make_payer(db_session, patient_aetna, "Aetna Commercial", "COMMERCIAL")
    claim_aetna = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient_aetna.id,
        billing_cycle_id=cycle2.id,
        status="PAID",
        payer_name="Aetna Commercial",
        total_charge=Decimal("100.00"),
        exported_days_ago=5,
    )
    _make_payment(db_session, tenant_id=tenant_id, remittance_advice_id=ra.id, claim_id=claim_aetna.id, paid_amount=Decimal("150.00"))

    headers = _headers("BILLING", tenant_id)
    for claim in (claim_medicare, claim_aetna):
        client.post("/billing/credit-balance/cases", headers=headers, json={"claim_id": str(claim.id)})

    export_response = client.get(
        "/billing/credit-balance/cms-838-export",
        headers=headers,
        params={"tenant_id": str(tenant_id)},
    )
    assert export_response.status_code == 200, export_response.text
    payload = export_response.json()
    assert payload["data_completeness"] == "PARTIAL"
    assert len(payload["rows"]) == 1
    assert payload["rows"][0]["icn"] == claim_medicare.claim_control_number
