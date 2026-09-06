from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.billing.models.billing_provider_agency_assignment import (
    BillingProviderAgencyAssignment,
    BillingProviderAgencyServiceScope,
)
from app.billing.models.billing_provider_organization import BillingProviderOrganization
from app.billing.models.billing_provider_organization_membership import (
    BillingProviderOrganizationMembership,
)
from app.billing.models.facility_payment_allocation import FacilityPaymentAllocation
from app.billing.services import facility_payment_service
from app.billing.services.billing_provider_access_service import (
    compute_tenant_financials_enabled,
)
from app.models.tenant import Tenant
from app.models.user import User
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
from tests.test_facility_payment_visibility import (
    _create_expectation,
    _make_patient_pos,
)


@pytest.fixture(autouse=True)
def _reset_test_user_membership(db_session, tenant):
    db_session.query(BillingProviderOrganizationMembership).filter(
        BillingProviderOrganizationMembership.user_id == TEST_USER_ID
    ).delete(synchronize_session=False)
    user = db_session.get(User, TEST_USER_ID)
    user.tenant_id = uuid.UUID(str(tenant.id))
    user.role = "RN"
    db_session.commit()
    yield
    db_session.query(BillingProviderOrganizationMembership).filter(
        BillingProviderOrganizationMembership.user_id == TEST_USER_ID
    ).delete(synchronize_session=False)
    user = db_session.get(User, TEST_USER_ID)
    user.tenant_id = uuid.UUID(str(tenant.id))
    user.role = "RN"
    db_session.commit()


def _owner_headers(tenant_id: uuid.UUID) -> dict[str, str]:
    return _headers("OWNER", tenant_id)


def _make_agency_tenant(db_session, *, legal_name: str) -> uuid.UUID:
    tenant_id = uuid.uuid4()
    return uuid.UUID(
        str(_enable_billing_for_tenant(db_session, tenant_id, legal_name=legal_name).id)
    )


def _make_provider_tenant(db_session) -> uuid.UUID:
    tenant_id = uuid.uuid4()
    db_session.add(
        Tenant(
            id=tenant_id,
            legal_name=f"Managed Billing Tenant {tenant_id.hex[:8]}",
            display_name=f"Managed Billing Tenant {tenant_id.hex[:8]}",
            npi=f"{str(tenant_id.int)[:10]:0>10}",
            tenant_type="BILLING",
            status="ACTIVE",
            created_by=TEST_USER_ID,
        )
    )
    db_session.commit()
    return tenant_id


def _make_billing_provider_organization(
    db_session,
    *,
    status: str = "ACTIVE",
    name: str = "North East Billing",
) -> BillingProviderOrganization:
    row = BillingProviderOrganization(
        id=uuid.uuid4(),
        name=f"{name} {uuid.uuid4().hex[:8]}",
        organization_type="MANAGED_BILLING_PROVIDER",
        status=status,
        created_by=TEST_USER_ID,
        updated_by=TEST_USER_ID,
    )
    db_session.add(row)
    db_session.commit()
    return row


def _set_user_role_and_tenant(
    db_session,
    *,
    tenant_id: uuid.UUID,
    role: str,
) -> None:
    user = db_session.get(User, TEST_USER_ID)
    user.tenant_id = tenant_id
    user.role = role
    db_session.commit()


def _create_membership(
    db_session,
    *,
    provider_org_id: uuid.UUID,
    user_id: uuid.UUID = TEST_USER_ID,
    membership_role: str = "MEMBER",
    status: str = "ACTIVE",
    effective_start_at: datetime | None = None,
    effective_end_at: datetime | None = None,
) -> BillingProviderOrganizationMembership:
    row = BillingProviderOrganizationMembership(
        id=uuid.uuid4(),
        billing_provider_organization_id=provider_org_id,
        user_id=user_id,
        membership_role=membership_role,
        status=status,
        effective_start_at=effective_start_at
        or (datetime.now(timezone.utc) - timedelta(days=1)),
        effective_end_at=effective_end_at,
        created_by=TEST_USER_ID,
        updated_by=TEST_USER_ID,
    )
    db_session.add(row)
    db_session.commit()
    return row


def _create_assignment(
    db_session,
    *,
    provider_org_id: uuid.UUID,
    tenant_id: uuid.UUID,
    relationship_status: str = "ACTIVE",
    service_scopes: list[str] | None = None,
    effective_start_at: datetime | None = None,
    effective_end_at: datetime | None = None,
) -> BillingProviderAgencyAssignment:
    row = BillingProviderAgencyAssignment(
        id=uuid.uuid4(),
        billing_provider_organization_id=provider_org_id,
        tenant_id=tenant_id,
        relationship_status=relationship_status,
        effective_start_at=effective_start_at
        or (datetime.now(timezone.utc) - timedelta(days=1)),
        effective_end_at=effective_end_at,
        created_by=TEST_USER_ID,
        updated_by=TEST_USER_ID,
    )
    db_session.add(row)
    db_session.flush()
    scopes = ["FACILITY_COLLECTIONS"] if service_scopes is None else service_scopes
    for scope in scopes:
        db_session.add(
            BillingProviderAgencyServiceScope(
                assignment_id=row.id,
                scope=scope,
            )
        )
    db_session.commit()
    return row


def _make_facility_expectation(db_session, tenant_id: uuid.UUID, *, mrn_prefix: str):
    patient = _make_patient(db_session, tenant_id, mrn_prefix=mrn_prefix)
    pos = _make_patient_pos(
        db_session,
        tenant_id,
        patient.id,
        pos_type="SNF",
        facility_name=f"{mrn_prefix} SNF",
        effective_date=date(2026, 3, 1),
    )
    expectation = _create_expectation(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        patient_pos_id=pos.id,
        authorization_reference=f"{mrn_prefix}-AUTH",
    )
    return patient, expectation


def _make_payment_posting_data(db_session, tenant_id: uuid.UUID, *, claim_prefix: str):
    cycle = _make_billing_cycle(db_session, tenant_id, month=4)
    patient = _make_patient(db_session, tenant_id, mrn_prefix=claim_prefix)
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
    remittance = _make_remittance(db_session, tenant_id)
    payment = _make_payment(
        db_session,
        tenant_id=tenant_id,
        remittance_advice_id=remittance.id,
        claim_id=claim.id,
        paid_amount=Decimal("150.00"),
    )
    return patient, claim, remittance, payment


def _make_confirmable_allocation(db_session, tenant_id: uuid.UUID) -> FacilityPaymentAllocation:
    cycle = _make_billing_cycle(db_session, tenant_id, month=6)
    patient = _make_patient(db_session, tenant_id, mrn_prefix="ALLOC")
    pos = _make_patient_pos(
        db_session,
        tenant_id,
        patient.id,
        pos_type="SNF",
        facility_name="Confirmable SNF",
        effective_date=date(2026, 6, 1),
    )
    claim = _make_claim(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        billing_cycle_id=cycle.id,
        status="PAID",
        payer_name="Medi-Cal",
        total_charge=Decimal("1000.00"),
        exported_days_ago=1,
    )
    claim.claim_control_number = "FAC-ALLOC-1"
    db_session.commit()
    remittance = _make_remittance(
        db_session,
        tenant_id,
        payer_name="Medi-Cal",
        payment_date="20260620",
    )
    payment = _make_payment(
        db_session,
        tenant_id=tenant_id,
        remittance_advice_id=remittance.id,
        claim_id=claim.id,
        paid_amount=Decimal("1000.00"),
        payment_date="20260620",
    )
    payment.claim_control_number = "FAC-ALLOC-1"
    db_session.commit()
    expectation = _create_expectation(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        patient_pos_id=pos.id,
        authorization_reference="FAC-ALLOC-1",
    )
    candidates = facility_payment_service.find_candidate_matches(
        db_session, expectation=expectation
    )
    return db_session.get(FacilityPaymentAllocation, candidates[0].id)


def _activate_financials(
    client,
    *,
    owner_tenant_id: uuid.UUID,
    target_tenant_id: uuid.UUID,
    provider_org_id: uuid.UUID,
    service_scopes: list[str],
    effective_start_at: datetime | None = None,
    effective_end_at: datetime | None = None,
    change_reason: str | None = None,
):
    payload = {
        "financials_enabled": True,
        "billing_provider_organization_id": str(provider_org_id),
        "effective_start_at": (
            effective_start_at or (datetime.now(timezone.utc) - timedelta(minutes=5))
        ).isoformat(),
        "service_scopes": service_scopes,
    }
    if effective_end_at is not None:
        payload["effective_end_at"] = effective_end_at.isoformat()
    if change_reason is not None:
        payload["change_reason"] = change_reason
    return client.patch(
        f"/api/owner/tenants/{target_tenant_id}/financials",
        headers=_owner_headers(owner_tenant_id),
        json=payload,
    )


def _deactivate_financials(
    client,
    *,
    owner_tenant_id: uuid.UUID,
    target_tenant_id: uuid.UUID,
    effective_end_at: datetime | None = None,
    change_reason: str | None = None,
):
    payload: dict[str, object] = {"financials_enabled": False}
    if effective_end_at is not None:
        payload["effective_end_at"] = effective_end_at.isoformat()
    if change_reason is not None:
        payload["change_reason"] = change_reason
    return client.patch(
        f"/api/owner/tenants/{target_tenant_id}/financials",
        headers=_owner_headers(owner_tenant_id),
        json=payload,
    )


def test_tenant_financials_is_computed_false_without_active_assignment(db_session):
    tenant_id = _make_agency_tenant(db_session, legal_name="Computed Off Agency")
    assert compute_tenant_financials_enabled(db_session, tenant_id) is False


def test_tenant_financials_is_computed_true_with_valid_active_assignment_and_scope(db_session):
    tenant_id = _make_agency_tenant(db_session, legal_name="Computed On Agency")
    provider_org = _make_billing_provider_organization(db_session)
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
        service_scopes=["FACILITY_COLLECTIONS"],
    )
    assert compute_tenant_financials_enabled(db_session, tenant_id) is True


@pytest.mark.parametrize(
    ("effective_start_at", "effective_end_at"),
    [
        (datetime.now(timezone.utc) + timedelta(days=1), None),
        (
            datetime.now(timezone.utc) - timedelta(days=10),
            datetime.now(timezone.utc) - timedelta(days=1),
        ),
    ],
)
def test_tenant_financials_is_false_outside_assignment_effective_window(
    db_session,
    effective_start_at,
    effective_end_at,
):
    tenant_id = _make_agency_tenant(db_session, legal_name="Windowed Financials Agency")
    provider_org = _make_billing_provider_organization(db_session)
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
        effective_start_at=effective_start_at,
        effective_end_at=effective_end_at,
    )
    assert compute_tenant_financials_enabled(db_session, tenant_id) is False


def test_tenant_financials_is_false_when_provider_is_inactive(db_session):
    tenant_id = _make_agency_tenant(db_session, legal_name="Inactive Provider Agency")
    provider_org = _make_billing_provider_organization(db_session, status="INACTIVE")
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
    )
    assert compute_tenant_financials_enabled(db_session, tenant_id) is False


def test_tenant_financials_is_false_when_assignment_has_no_scopes(db_session):
    tenant_id = _make_agency_tenant(db_session, legal_name="No Scope Financials Agency")
    provider_org = _make_billing_provider_organization(db_session)
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
        service_scopes=[],
    )
    assert compute_tenant_financials_enabled(db_session, tenant_id) is False


def test_tenant_financials_is_not_a_stored_tenant_column():
    assert not hasattr(Tenant, "financials_enabled")


def test_owner_financials_activation_creates_assignment_and_computed_true(
    client,
    db_session,
    tenant,
):
    target_tenant_id = _make_agency_tenant(db_session, legal_name="Owner Activation Agency")
    provider_org = _make_billing_provider_organization(db_session)

    response = _activate_financials(
        client,
        owner_tenant_id=uuid.UUID(str(tenant.id)),
        target_tenant_id=target_tenant_id,
        provider_org_id=provider_org.id,
        service_scopes=["FACILITY_COLLECTIONS", "PAYMENT_POSTING"],
        change_reason="Enable managed billing",
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["financials_enabled"] is True
    assignments = (
        db_session.query(BillingProviderAgencyAssignment)
        .filter(BillingProviderAgencyAssignment.tenant_id == target_tenant_id)
        .all()
    )
    assert len(assignments) == 1
    assert assignments[0].relationship_status == "ACTIVE"
    assert {scope.scope for scope in assignments[0].service_scopes} == {
        "FACILITY_COLLECTIONS",
        "PAYMENT_POSTING",
    }


def test_owner_financials_deactivation_terminates_assignment_and_preserves_history(
    client,
    db_session,
    tenant,
):
    target_tenant_id = _make_agency_tenant(db_session, legal_name="Owner Deactivation Agency")
    provider_org = _make_billing_provider_organization(db_session)
    activate = _activate_financials(
        client,
        owner_tenant_id=uuid.UUID(str(tenant.id)),
        target_tenant_id=target_tenant_id,
        provider_org_id=provider_org.id,
        service_scopes=["FACILITY_COLLECTIONS"],
    )
    assert activate.status_code == 200, activate.text

    deactivate = _deactivate_financials(
        client,
        owner_tenant_id=uuid.UUID(str(tenant.id)),
        target_tenant_id=target_tenant_id,
        change_reason="End provider assignment",
    )

    assert deactivate.status_code == 200, deactivate.text
    payload = deactivate.json()
    assert payload["financials_enabled"] is False
    assignment = (
        db_session.query(BillingProviderAgencyAssignment)
        .filter(BillingProviderAgencyAssignment.tenant_id == target_tenant_id)
        .one()
    )
    assert assignment.relationship_status == "TERMINATED"
    assert assignment.effective_end_at is not None
    assert db_session.get(BillingProviderAgencyAssignment, assignment.id) is not None


def test_billing_role_without_membership_is_denied(client, db_session):
    tenant_id = _make_agency_tenant(db_session, legal_name="No Membership Agency")
    _make_facility_expectation(db_session, tenant_id, mrn_prefix="NOMEM")
    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
        service_scopes=["FACILITY_COLLECTIONS"],
    )
    _set_user_role_and_tenant(db_session, tenant_id=provider_tenant_id, role="BILLING")

    response = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )

    assert response.status_code == 403


def test_inactive_membership_is_denied(client, db_session):
    tenant_id = _make_agency_tenant(db_session, legal_name="Inactive Membership Agency")
    _make_facility_expectation(db_session, tenant_id, mrn_prefix="INACTM")
    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
    )
    _create_membership(
        db_session,
        provider_org_id=provider_org.id,
        status="INACTIVE",
    )
    _set_user_role_and_tenant(db_session, tenant_id=provider_tenant_id, role="PLATFORM_BILLING")

    response = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )

    assert response.status_code == 403


def test_expired_membership_is_denied(client, db_session):
    tenant_id = _make_agency_tenant(db_session, legal_name="Expired Membership Agency")
    _make_facility_expectation(db_session, tenant_id, mrn_prefix="EXPMEM")
    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
    )
    _create_membership(
        db_session,
        provider_org_id=provider_org.id,
        effective_start_at=datetime.now(timezone.utc) - timedelta(days=10),
        effective_end_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    _set_user_role_and_tenant(db_session, tenant_id=provider_tenant_id, role="PLATFORM_BILLING")

    response = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )

    assert response.status_code == 403


def test_active_membership_plus_active_assignment_succeeds(client, db_session):
    tenant_id = _make_agency_tenant(db_session, legal_name="Active Membership Agency")
    _, expectation = _make_facility_expectation(db_session, tenant_id, mrn_prefix="ACTMEM")
    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
        service_scopes=["FACILITY_COLLECTIONS"],
    )
    _create_membership(db_session, provider_org_id=provider_org.id)
    _set_user_role_and_tenant(db_session, tenant_id=provider_tenant_id, role="BILLING")

    response = client.get(
        f"/billing/facility-payments/expectations/{expectation.id}",
        headers=_headers("BILLING", provider_tenant_id),
    )

    assert response.status_code == 200, response.text
    assert response.json()["tenant_id"] == str(tenant_id)


def test_client_supplied_provider_id_does_not_bypass_membership_lookup(client, db_session):
    tenant_id = _make_agency_tenant(db_session, legal_name="Bypass Attempt Agency")
    _make_facility_expectation(db_session, tenant_id, mrn_prefix="BYPASS")
    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _create_assignment(db_session, provider_org_id=provider_org.id, tenant_id=tenant_id)
    _set_user_role_and_tenant(db_session, tenant_id=provider_tenant_id, role="PLATFORM_BILLING")

    response = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={
            "tenant_id": str(tenant_id),
            "billing_provider_organization_id": str(provider_org.id),
        },
    )

    assert response.status_code == 403


def test_facility_collections_scope_does_not_grant_payment_posting(client, db_session):
    tenant_id = _make_agency_tenant(db_session, legal_name="Facility Scope Agency")
    _make_facility_expectation(db_session, tenant_id, mrn_prefix="FCPOST")
    _make_payment_posting_data(db_session, tenant_id, claim_prefix="FCPOST")
    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _create_membership(db_session, provider_org_id=provider_org.id)
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
        service_scopes=["FACILITY_COLLECTIONS"],
    )
    _set_user_role_and_tenant(db_session, tenant_id=provider_tenant_id, role="PLATFORM_BILLING")

    facility = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )
    remittances = client.get(
        "/billing/remittances",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )

    assert facility.status_code == 200, facility.text
    assert remittances.status_code == 403


def test_payment_posting_scope_does_not_grant_facility_collections_or_credit_balances(
    client,
    db_session,
):
    tenant_id = _make_agency_tenant(db_session, legal_name="Posting Scope Agency")
    _make_facility_expectation(db_session, tenant_id, mrn_prefix="POSTING")
    _make_payment_posting_data(db_session, tenant_id, claim_prefix="POSTING")
    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _create_membership(db_session, provider_org_id=provider_org.id)
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
        service_scopes=["PAYMENT_POSTING"],
    )
    _set_user_role_and_tenant(db_session, tenant_id=provider_tenant_id, role="PLATFORM_BILLING")

    remittances = client.get(
        "/billing/remittances",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )
    facility = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )
    credit = client.get(
        "/billing/credit-balance/report",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )

    assert remittances.status_code == 200, remittances.text
    assert facility.status_code == 403
    assert credit.status_code == 403


def test_credit_balances_scope_does_not_grant_aging_report(client, db_session):
    tenant_id = _make_agency_tenant(db_session, legal_name="Credit Scope Agency")
    _make_payment_posting_data(db_session, tenant_id, claim_prefix="CREDIT")
    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _create_membership(db_session, provider_org_id=provider_org.id)
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
        service_scopes=["CREDIT_BALANCES"],
    )
    _set_user_role_and_tenant(db_session, tenant_id=provider_tenant_id, role="PLATFORM_BILLING")

    credit = client.get(
        "/billing/credit-balance/report",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )
    aging = client.get(
        "/billing/aging-report",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )

    assert credit.status_code == 200, credit.text
    assert aging.status_code == 403


def test_financial_monitoring_scope_does_not_grant_operational_edit_confirm_allocation(
    client,
    db_session,
):
    tenant_id = _make_agency_tenant(db_session, legal_name="Monitoring Scope Agency")
    allocation = _make_confirmable_allocation(db_session, tenant_id)
    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _create_membership(db_session, provider_org_id=provider_org.id)
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
        service_scopes=["FINANCIAL_MONITORING"],
    )
    _set_user_role_and_tenant(db_session, tenant_id=provider_tenant_id, role="PLATFORM_BILLING")

    response = client.post(
        f"/billing/facility-payments/allocations/{allocation.id}/confirm",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
    )

    assert response.status_code == 403


def test_facility_collections_scope_does_not_grant_payment_reconciliation_confirm(
    client,
    db_session,
):
    tenant_id = _make_agency_tenant(db_session, legal_name="Facility Readonly Scope Agency")
    allocation = _make_confirmable_allocation(db_session, tenant_id)
    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _create_membership(db_session, provider_org_id=provider_org.id)
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
        service_scopes=["FACILITY_COLLECTIONS"],
    )
    _set_user_role_and_tenant(db_session, tenant_id=provider_tenant_id, role="BILLING")

    response = client.post(
        f"/billing/facility-payments/allocations/{allocation.id}/confirm",
        headers=_headers("BILLING", provider_tenant_id),
    )

    assert response.status_code == 403


def test_platform_billing_can_view_but_cannot_edit_expectations(client, db_session):
    tenant_id = _make_agency_tenant(db_session, legal_name="Platform View Only Agency")
    patient, expectation = _make_facility_expectation(db_session, tenant_id, mrn_prefix="PVONLY")
    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _create_membership(db_session, provider_org_id=provider_org.id)
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
        service_scopes=["FACILITY_COLLECTIONS"],
    )
    _set_user_role_and_tenant(db_session, tenant_id=provider_tenant_id, role="PLATFORM_BILLING")

    read_response = client.get(
        f"/billing/facility-payments/expectations/{expectation.id}",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
    )
    create_response = client.post(
        f"/billing/facility-payments/expectations?tenant_id={tenant_id}",
        json={
            "patient_id": str(patient.id),
            "responsibility_category": "ROOM_AND_BOARD",
            "expected_funding_source": "MEDICAID_FFS",
            "expected_amount": "100.00",
            "service_period_start": "2026-04-01",
            "service_period_end": "2026-04-30",
            "source": "AUTHORIZED_MANUAL_ENTRY",
        },
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
    )

    assert read_response.status_code == 200, read_response.text
    assert create_response.status_code == 403


def test_corrected_credit_balance_and_aging_scope_mappings_require_their_own_scopes(
    client,
    db_session,
):
    tenant_id = _make_agency_tenant(db_session, legal_name="Corrected Scope Agency")
    _make_payment_posting_data(db_session, tenant_id, claim_prefix="CORR")
    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _create_membership(db_session, provider_org_id=provider_org.id)
    _set_user_role_and_tenant(db_session, tenant_id=provider_tenant_id, role="PLATFORM_BILLING")

    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
        service_scopes=["PAYMENT_RECONCILIATION"],
    )
    credit = client.get(
        "/billing/credit-balance/report",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )
    assert credit.status_code == 403

    assignment = (
        db_session.query(BillingProviderAgencyAssignment)
        .filter(BillingProviderAgencyAssignment.tenant_id == tenant_id)
        .one()
    )
    assignment.service_scopes[:] = [BillingProviderAgencyServiceScope(scope="FINANCIAL_MONITORING")]
    db_session.commit()

    aging = client.get(
        "/billing/aging-report",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )
    assert aging.status_code == 403


def test_cross_tenant_denial_applies_to_all_billing_routers(client, db_session):
    assigned_tenant = _make_agency_tenant(db_session, legal_name="Assigned Router Agency")
    unassigned_tenant = _make_agency_tenant(db_session, legal_name="Unassigned Router Agency")
    _make_facility_expectation(db_session, assigned_tenant, mrn_prefix="ASSIGNED")
    _make_facility_expectation(db_session, unassigned_tenant, mrn_prefix="UNASSGN")
    _make_payment_posting_data(db_session, assigned_tenant, claim_prefix="ASSIGNED")
    _make_payment_posting_data(db_session, unassigned_tenant, claim_prefix="UNASSGN")

    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _create_membership(db_session, provider_org_id=provider_org.id)
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=assigned_tenant,
        service_scopes=[
            "FACILITY_COLLECTIONS",
            "PAYMENT_POSTING",
            "CREDIT_BALANCES",
            "AGING_REPORT",
        ],
    )
    _set_user_role_and_tenant(db_session, tenant_id=provider_tenant_id, role="PLATFORM_BILLING")

    for path in (
        "/billing/facility-payments/expectations",
        "/billing/remittances",
        "/billing/credit-balance/report",
        "/billing/aging-report",
    ):
        response = client.get(
            path,
            headers=_headers("PLATFORM_BILLING", provider_tenant_id),
            params={"tenant_id": str(unassigned_tenant)},
        )
        assert response.status_code == 403, f"{path}: {response.text}"


def test_all_agencies_query_returns_only_assigned_tenants(client, db_session):
    assigned_tenant = _make_agency_tenant(db_session, legal_name="Assigned All Agency")
    unassigned_tenant = _make_agency_tenant(db_session, legal_name="Unassigned All Agency")
    _, assigned_expectation = _make_facility_expectation(
        db_session, assigned_tenant, mrn_prefix="ALLA"
    )
    _make_facility_expectation(db_session, unassigned_tenant, mrn_prefix="ALLB")

    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _create_membership(db_session, provider_org_id=provider_org.id)
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=assigned_tenant,
        service_scopes=["FACILITY_COLLECTIONS"],
    )
    _set_user_role_and_tenant(db_session, tenant_id=provider_tenant_id, role="PLATFORM_BILLING")

    response = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"all_agencies": "true"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["count"] == 1
    assert payload["items"][0]["id"] == str(assigned_expectation.id)
    assert {item["tenant_id"] for item in payload["items"]} == {str(assigned_tenant)}


def test_financials_off_immediately_revokes_managed_billing_access(
    client,
    db_session,
    tenant,
):
    target_tenant_id = _make_agency_tenant(db_session, legal_name="Immediate Off Agency")
    _make_facility_expectation(db_session, target_tenant_id, mrn_prefix="OFFNOW")
    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _create_membership(db_session, provider_org_id=provider_org.id)
    _set_user_role_and_tenant(db_session, tenant_id=provider_tenant_id, role="PLATFORM_BILLING")

    activate = _activate_financials(
        client,
        owner_tenant_id=uuid.UUID(str(tenant.id)),
        target_tenant_id=target_tenant_id,
        provider_org_id=provider_org.id,
        service_scopes=["FACILITY_COLLECTIONS"],
    )
    assert activate.status_code == 200, activate.text

    before = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(target_tenant_id)},
    )
    assert before.status_code == 200, before.text

    deactivate = _deactivate_financials(
        client,
        owner_tenant_id=uuid.UUID(str(tenant.id)),
        target_tenant_id=target_tenant_id,
    )
    assert deactivate.status_code == 200, deactivate.text

    after = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(target_tenant_id)},
    )
    assert after.status_code == 403


def test_financials_off_preserves_agency_own_tenant_billing_access(client, db_session, tenant):
    tenant_id = _make_agency_tenant(db_session, legal_name="Tenant Billing Preserved Agency")
    _, expectation = _make_facility_expectation(db_session, tenant_id, mrn_prefix="OWNTEN")
    provider_org = _make_billing_provider_organization(db_session)
    activate = _activate_financials(
        client,
        owner_tenant_id=uuid.UUID(str(tenant.id)),
        target_tenant_id=tenant_id,
        provider_org_id=provider_org.id,
        service_scopes=["FACILITY_COLLECTIONS"],
    )
    assert activate.status_code == 200, activate.text
    deactivate = _deactivate_financials(
        client,
        owner_tenant_id=uuid.UUID(str(tenant.id)),
        target_tenant_id=tenant_id,
    )
    assert deactivate.status_code == 200, deactivate.text
    _set_user_role_and_tenant(db_session, tenant_id=tenant_id, role="BILLING")

    response = client.get(
        f"/billing/facility-payments/expectations/{expectation.id}",
        headers=_headers("BILLING", tenant_id),
    )

    assert response.status_code == 200, response.text
    assert response.json()["tenant_id"] == str(tenant_id)


def test_financials_on_grants_only_selected_scopes(client, db_session, tenant):
    target_tenant_id = _make_agency_tenant(db_session, legal_name="Selected Scope Agency")
    _make_facility_expectation(db_session, target_tenant_id, mrn_prefix="SCOPED")
    _make_payment_posting_data(db_session, target_tenant_id, claim_prefix="SCOPED")
    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _create_membership(db_session, provider_org_id=provider_org.id)
    _set_user_role_and_tenant(db_session, tenant_id=provider_tenant_id, role="PLATFORM_BILLING")

    activate = _activate_financials(
        client,
        owner_tenant_id=uuid.UUID(str(tenant.id)),
        target_tenant_id=target_tenant_id,
        provider_org_id=provider_org.id,
        service_scopes=["FACILITY_COLLECTIONS"],
    )
    assert activate.status_code == 200, activate.text

    facility = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(target_tenant_id)},
    )
    remittances = client.get(
        "/billing/remittances",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(target_tenant_id)},
    )
    credit = client.get(
        "/billing/credit-balance/report",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(target_tenant_id)},
    )
    aging = client.get(
        "/billing/aging-report",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(target_tenant_id)},
    )

    assert facility.status_code == 200, facility.text
    assert remittances.status_code == 403
    assert credit.status_code == 403
    assert aging.status_code == 403


def test_provider_change_preserves_terminated_history_row(client, db_session, tenant):
    target_tenant_id = _make_agency_tenant(db_session, legal_name="Provider Change Agency")
    provider_a = _make_billing_provider_organization(db_session, name="Provider A")
    provider_b = _make_billing_provider_organization(db_session, name="Provider B")

    activate_a = _activate_financials(
        client,
        owner_tenant_id=uuid.UUID(str(tenant.id)),
        target_tenant_id=target_tenant_id,
        provider_org_id=provider_a.id,
        service_scopes=["FACILITY_COLLECTIONS"],
    )
    assert activate_a.status_code == 200, activate_a.text

    deactivate = _deactivate_financials(
        client,
        owner_tenant_id=uuid.UUID(str(tenant.id)),
        target_tenant_id=target_tenant_id,
    )
    assert deactivate.status_code == 200, deactivate.text

    activate_b = _activate_financials(
        client,
        owner_tenant_id=uuid.UUID(str(tenant.id)),
        target_tenant_id=target_tenant_id,
        provider_org_id=provider_b.id,
        service_scopes=["FACILITY_COLLECTIONS"],
    )
    assert activate_b.status_code == 200, activate_b.text

    assignments = (
        db_session.query(BillingProviderAgencyAssignment)
        .filter(BillingProviderAgencyAssignment.tenant_id == target_tenant_id)
        .order_by(BillingProviderAgencyAssignment.created_at.asc())
        .all()
    )
    assert len(assignments) == 2
    assert assignments[0].billing_provider_organization_id == provider_a.id
    assert assignments[0].relationship_status == "TERMINATED"
    assert assignments[1].billing_provider_organization_id == provider_b.id
    assert assignments[1].relationship_status == "ACTIVE"


def test_conflicting_overlapping_assignments_from_second_provider_are_rejected(
    client,
    db_session,
    tenant,
):
    target_tenant_id = _make_agency_tenant(db_session, legal_name="Conflict Agency")
    provider_a = _make_billing_provider_organization(db_session, name="Provider A")
    provider_b = _make_billing_provider_organization(db_session, name="Provider B")

    first = _activate_financials(
        client,
        owner_tenant_id=uuid.UUID(str(tenant.id)),
        target_tenant_id=target_tenant_id,
        provider_org_id=provider_a.id,
        service_scopes=["FACILITY_COLLECTIONS"],
    )
    assert first.status_code == 200, first.text

    second = _activate_financials(
        client,
        owner_tenant_id=uuid.UUID(str(tenant.id)),
        target_tenant_id=target_tenant_id,
        provider_org_id=provider_b.id,
        service_scopes=["FACILITY_COLLECTIONS"],
    )
    assert second.status_code == 409, second.text


def test_platform_billing_reaches_billing_route_but_endpoint_still_returns_403(
    client,
    db_session,
):
    tenant_id = _make_agency_tenant(db_session, legal_name="Middleware Reach Agency")
    _make_facility_expectation(db_session, tenant_id, mrn_prefix="MW403")
    provider_tenant_id = _make_provider_tenant(db_session)
    _set_user_role_and_tenant(db_session, tenant_id=provider_tenant_id, role="PLATFORM_BILLING")

    response = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )

    assert response.status_code == 403
    assert "clinical access" not in response.text.lower()


def test_platform_billing_cannot_reach_unrelated_clinical_routes(client, db_session):
    provider_tenant_id = _make_provider_tenant(db_session)
    _set_user_role_and_tenant(db_session, tenant_id=provider_tenant_id, role="PLATFORM_BILLING")

    response = client.get(
        "/patients",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Clinical access is not permitted for this role."


def test_clinical_only_tenant_role_cannot_access_financial_routes(client, db_session):
    tenant_id = _make_agency_tenant(db_session, legal_name="Clinical Denial Agency")
    _make_facility_expectation(db_session, tenant_id, mrn_prefix="CLIN")
    _set_user_role_and_tenant(db_session, tenant_id=tenant_id, role="RN")

    response = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("RN", tenant_id),
    )

    assert response.status_code == 403
