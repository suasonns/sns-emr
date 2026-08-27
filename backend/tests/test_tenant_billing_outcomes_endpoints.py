from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from app.billing.models.appeal import Appeal
from app.billing.models.billing_cycle import BillingCycle
from app.billing.models.claim import Claim
from app.billing.models.denial import Denial
from app.core.security import create_access_token
from app.models.admission import Admission
from app.models.benefit_period import BenefitPeriod
from app.models.certification import Certification
from app.models.patient import Patient
from app.models.patient_payer import PatientPayer
from app.models.plan_of_care import PlanOfCare
from app.models.plan_of_care_version import PlanOfCareVersion
from app.models.poc_physician_approval import PocPhysicianApproval
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


def _enable_billing_for_tenant(
    db_session,
    tenant_id: uuid.UUID,
    *,
    legal_name: str,
    display_name: str,
) -> Tenant:
    tenant = db_session.get(Tenant, tenant_id)
    if tenant is None:
        tenant = Tenant(
            id=tenant_id,
            legal_name=legal_name,
            display_name=display_name,
            npi=f"{str(tenant_id.int)[:10]:0>10}",
            tenant_type="DEV",
            status="ACTIVE",
        )
        db_session.add(tenant)
    tenant.legal_name = legal_name
    tenant.display_name = display_name
    tenant.tenant_type = "DEV"
    tenant.status = "ACTIVE"
    tenant.billing_enabled = True
    tenant.ein = "123456789"
    tenant.ptan = f"P{str(tenant_id.int)[:7]}"
    db_session.commit()
    return tenant


def _make_patient(
    db_session,
    tenant_id: uuid.UUID,
    *,
    mrn_prefix: str,
    diagnosis: str = "J44.9",
) -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"{mrn_prefix}-{uuid.uuid4().hex[:8]}",
        date_of_birth=date(1946, 6, 6),
        primary_diagnosis=diagnosis,
        status="ACTIVE",
        election_signed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_billing_cycle(
    db_session,
    tenant_id: uuid.UUID,
    *,
    month: int,
    year: int = 2026,
) -> BillingCycle:
    cycle = BillingCycle(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        month=month,
        year=year,
        start_date=date(year, month, 1),
        end_date=date(year, month, 28 if month == 2 else 30 if month in {4, 6, 9, 11} else 31),
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
    payer_name: str = "Medicare",
    total_charge: Decimal = Decimal("1250.00"),
) -> Claim:
    claim = Claim(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        billing_cycle_id=billing_cycle_id,
        payer_name=payer_name,
        service_date=date(2026, 3, 15),
        total_charge=total_charge,
        total_units=4,
        risk_score=0,
        status=status,
        created_by="test-suite",
    )
    db_session.add(claim)
    db_session.commit()
    return claim


def _make_denial(
    db_session,
    *,
    tenant_id: uuid.UUID,
    claim_id: uuid.UUID,
    status: str,
    carc_code: str,
    denied_amount: Decimal,
    reason_description: str,
) -> Denial:
    denial = Denial(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        claim_id=claim_id,
        carc_code=carc_code,
        denied_amount=denied_amount,
        denial_date=date(2026, 3, 20),
        appeal_deadline=date(2026, 4, 20),
        status=status,
        reason_description=reason_description,
    )
    db_session.add(denial)
    db_session.commit()
    return denial


def _make_appeal(
    db_session,
    *,
    tenant_id: uuid.UUID,
    denial_id: uuid.UUID,
    status: str,
    outcome_amount: Decimal,
) -> Appeal:
    appeal = Appeal(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        denial_id=denial_id,
        level=1,
        status=status,
        submitted_date=date(2026, 3, 22),
        submitted_by="Billing Specialist",
        decision_date=date(2026, 3, 28),
        outcome_amount=outcome_amount,
        notes="Appeal packet sent with signed CTI and supporting documentation.",
    )
    db_session.add(appeal)
    db_session.commit()
    return appeal


def _make_benefit_period(db_session, tenant_id: uuid.UUID, patient: Patient) -> BenefitPeriod:
    period = BenefitPeriod(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        benefit_type="INITIAL",
        period_number=1,
        election_date=date(2026, 1, 1),
        start_date=date(2026, 1, 1),
        end_date=date(2026, 4, 30),
        is_current=True,
        noe_submitted_date=date(2026, 1, 2),
    )
    db_session.add(period)
    db_session.commit()
    return period


def _make_certification(db_session, tenant_id: uuid.UUID, patient: Patient, period: BenefitPeriod) -> None:
    db_session.add(
        Certification(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            patient_id=patient.id,
            benefit_period_id=period.id,
            cert_type="INITIAL",
            signed_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            effective_date=period.start_date,
            signed_by_role="MEDICAL_DIRECTOR",
            status="FINALIZED",
        )
    )
    db_session.commit()


def _make_approved_poc(db_session, tenant_id: uuid.UUID, patient: Patient) -> None:
    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        admission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(admission)
    db_session.commit()

    poc = PlanOfCare(
        id=uuid.uuid4(),
        admission_id=admission.id,
        patient_id=patient.id,
        tenant_id=tenant_id,
        status="ACTIVE",
    )
    db_session.add(poc)
    db_session.commit()

    version = PlanOfCareVersion(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        plan_of_care_id=poc.id,
        version_number=1,
        status="ACTIVE",
        source_kind="ICA",
    )
    db_session.add(version)
    db_session.commit()

    poc.current_version_id = version.id
    db_session.commit()

    db_session.add(
        PocPhysicianApproval(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            patient_id=patient.id,
            poc_version_id=version.id,
            physician_name="Dr. Raymond Atlas",
            physician_role="HOSPICE_MEDICAL_DIRECTOR",
            approval_method="UPLOADED_SIGNED_APPROVAL_DOCUMENT",
            approval_status="PHYSICIAN_APPROVED",
            approval_date=date(2026, 1, 2),
        )
    )
    db_session.commit()


def _make_payer(db_session, patient: Patient) -> None:
    db_session.add(
        PatientPayer(
            id=uuid.uuid4(),
            patient_id=patient.id,
            payer_name="MEDICARE",
            payer_type="MEDICARE",
            subscriber_id="1EG4TE5MK73",
            subscriber_id_type="MBI",
            is_primary=True,
            effective_start_date=date(2020, 1, 1),
        )
    )
    db_session.commit()


def test_claim_lifecycle_endpoint_returns_real_counts(client, db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(
        db_session,
        tenant_id,
        legal_name="Lifecycle Hospice",
        display_name="Lifecycle Hospice",
    )
    for index, status in enumerate(("READY", "SENT", "ACCEPTED", "PAID", "DENIED"), start=1):
        patient = _make_patient(db_session, tenant_id, mrn_prefix=f"CLAIM{index}")
        cycle = _make_billing_cycle(db_session, tenant_id, month=index)
        _make_claim(
            db_session,
            tenant_id=tenant_id,
            patient_id=patient.id,
            billing_cycle_id=cycle.id,
            status=status,
            total_charge=Decimal("1000.00"),
        )

    response = client.get(
        "/api/dashboard/claim-lifecycle",
        headers=_headers("BILLING", tenant_id),
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "ready": 1,
        "sent": 1,
        "accepted": 1,
        "paid": 1,
        "denied": 1,
    }


def test_denials_appeals_endpoint_returns_real_summary(client, db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(
        db_session,
        tenant_id,
        legal_name="Denial Hospice",
        display_name="Denial Hospice",
    )
    open_patient = _make_patient(db_session, tenant_id, mrn_prefix="DENIAL1")
    open_cycle = _make_billing_cycle(db_session, tenant_id, month=3)

    open_claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=open_patient.id,
        billing_cycle_id=open_cycle.id,
        status="DENIED",
        total_charge=Decimal("1500.00"),
    )
    appealed_patient = _make_patient(db_session, tenant_id, mrn_prefix="DENIAL2")
    appealed_cycle = _make_billing_cycle(db_session, tenant_id, month=4)
    appealed_claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=appealed_patient.id,
        billing_cycle_id=appealed_cycle.id,
        status="DENIED",
        total_charge=Decimal("1750.00"),
    )
    upheld_patient = _make_patient(db_session, tenant_id, mrn_prefix="DENIAL3")
    upheld_cycle = _make_billing_cycle(db_session, tenant_id, month=5)
    upheld_claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=upheld_patient.id,
        billing_cycle_id=upheld_cycle.id,
        status="DENIED",
        total_charge=Decimal("900.00"),
    )

    open_denial = _make_denial(
        db_session,
        tenant_id=tenant_id,
        claim_id=open_claim.id,
        status="OPEN",
        carc_code="16",
        denied_amount=Decimal("200.00"),
        reason_description="Claim/service lacks information needed for adjudication.",
    )
    appealed_denial = _make_denial(
        db_session,
        tenant_id=tenant_id,
        claim_id=appealed_claim.id,
        status="APPEALED",
        carc_code="96",
        denied_amount=Decimal("300.00"),
        reason_description="Non-covered charges.",
    )
    _make_denial(
        db_session,
        tenant_id=tenant_id,
        claim_id=upheld_claim.id,
        status="UPHELD",
        carc_code="16",
        denied_amount=Decimal("150.00"),
        reason_description="Claim/service lacks information needed for adjudication.",
    )
    _make_appeal(
        db_session,
        tenant_id=tenant_id,
        denial_id=appealed_denial.id,
        status="APPROVED",
        outcome_amount=Decimal("125.50"),
    )

    response = client.get(
        "/api/dashboard/denials-appeals",
        headers=_headers("RN", tenant_id),
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["open_denials"] == 1
    assert payload["appealed_denials"] == 1
    assert payload["upheld_denials"] == 1
    assert payload["overturned_denials"] == 0
    assert payload["written_off_denials"] == 0
    assert payload["total_denied_amount"] == 650.0
    assert payload["open_denied_amount"] == 200.0
    assert payload["total_recovered_amount"] == 125.5

    top_code_16 = next(row for row in payload["top_denial_codes"] if row["carc_code"] == "16")
    assert top_code_16["case_count"] == 2
    assert top_code_16["total_amount"] == 350.0
    top_code_96 = next(row for row in payload["top_denial_codes"] if row["carc_code"] == "96")
    assert top_code_96["case_count"] == 1
    assert top_code_96["total_amount"] == 300.0


def test_billing_readiness_endpoint_returns_cross_agency_rollup(client, db_session, tenant):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(
        db_session,
        tenant_id,
        legal_name="Readiness Hospice",
        display_name="Readiness Hospice",
    )

    ready_patient = _make_patient(db_session, tenant_id, mrn_prefix="READY", diagnosis="C34.90")
    ready_period = _make_benefit_period(db_session, tenant_id, ready_patient)
    _make_certification(db_session, tenant_id, ready_patient, ready_period)
    _make_approved_poc(db_session, tenant_id, ready_patient)
    _make_payer(db_session, ready_patient)

    blocked_patient = _make_patient(db_session, tenant_id, mrn_prefix="BLOCK", diagnosis="R63.4")
    _make_benefit_period(db_session, tenant_id, blocked_patient)

    response = client.get(
        "/api/dashboard/billing-readiness",
        headers=_headers("OWNER", tenant_id),
        params={"service_date": "2026-03-15"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["total_agencies"] >= 1

    agency_row = next(row for row in payload["agencies"] if row["tenant_id"] == str(tenant_id))
    assert agency_row["billing_enabled"] is True
    assert agency_row["total_patients"] >= 2
    assert agency_row["ready_count"] >= 1
    assert agency_row["not_ready_count"] >= 1

    patient_rows = {row["patient_id"]: row for row in agency_row["patients"]}
    assert patient_rows[str(ready_patient.id)]["ready"] is True
    assert patient_rows[str(blocked_patient.id)]["ready"] is False

    blocker_categories = {entry["category"] for entry in payload["blocker_breakdown"]}
    assert "Missing Certification" in blocker_categories
    assert "Missing POC Physician Signature" in blocker_categories
