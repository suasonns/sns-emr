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
    user = db_session.get(User, TEST_USER_ID)
    user.tenant_id = uuid.UUID(str(tenant.id))
    user.role = "RN"
    user.billing_provider_organization_id = None
    db_session.commit()
    yield
    user = db_session.get(User, TEST_USER_ID)
    user.tenant_id = uuid.UUID(str(tenant.id))
    user.role = "RN"
    user.billing_provider_organization_id = None
    db_session.commit()


def _set_tenant_financials(db_session, tenant_id: uuid.UUID, enabled: bool) -> None:
    tenant = db_session.get(Tenant, tenant_id)
    tenant.financials_enabled = enabled
    db_session.commit()


def _make_billing_provider_organization(db_session, *, name: str = "North East Billing") -> BillingProviderOrganization:
    unique_name = f"{name} {uuid.uuid4().hex[:8]}"
    row = BillingProviderOrganization(
        id=uuid.uuid4(),
        name=unique_name,
        organization_type="MANAGED_BILLING_PROVIDER",
        status="ACTIVE",
        created_by=TEST_USER_ID,
        updated_by=TEST_USER_ID,
    )
    db_session.add(row)
    db_session.commit()
    return row


def _make_provider_tenant(db_session) -> uuid.UUID:
    tenant_id = uuid.uuid4()
    tenant = Tenant(
        id=tenant_id,
        legal_name="Managed Billing Provider",
        display_name="Managed Billing Provider",
        npi=f"{str(tenant_id.int)[:10]:0>10}",
        tenant_type="BILLING",
        status="ACTIVE",
    )
    db_session.add(tenant)
    db_session.commit()
    return tenant_id


def _set_platform_billing_user(
    db_session,
    *,
    provider_org_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> None:
    user = db_session.get(User, TEST_USER_ID)
    user.tenant_id = tenant_id
    user.role = "PLATFORM_BILLING"
    user.billing_provider_organization_id = provider_org_id
    db_session.commit()


def _set_tenant_billing_user(db_session, *, tenant_id: uuid.UUID) -> None:
    user = db_session.get(User, TEST_USER_ID)
    user.tenant_id = tenant_id
    user.role = "BILLING"
    user.billing_provider_organization_id = None
    db_session.commit()


def _create_assignment(
    db_session,
    *,
    provider_org_id: uuid.UUID,
    tenant_id: uuid.UUID,
    relationship_status: str = "ACTIVE",
    service_scopes: list[str] | None = None,
    assignment_financials_enabled: bool = True,
    effective_start_at: datetime | None = None,
    effective_end_at: datetime | None = None,
) -> BillingProviderAgencyAssignment:
    row = BillingProviderAgencyAssignment(
        id=uuid.uuid4(),
        billing_provider_organization_id=provider_org_id,
        tenant_id=tenant_id,
        relationship_status=relationship_status,
        effective_start_at=effective_start_at or (datetime.now(timezone.utc) - timedelta(days=1)),
        effective_end_at=effective_end_at,
        financials_enabled=assignment_financials_enabled,
        created_by=TEST_USER_ID,
        updated_by=TEST_USER_ID,
    )
    db_session.add(row)
    db_session.flush()
    for scope in service_scopes or ["FACILITY_COLLECTIONS"]:
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
    return _create_expectation(
        db_session,
        tenant_id=tenant_id,
        patient_id=patient.id,
        patient_pos_id=pos.id,
        authorization_reference=f"{mrn_prefix}-AUTH",
    )


def test_tenant_billing_user_keeps_own_facility_collections_access_when_financials_off(
    client,
    db_session,
    tenant,
):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Own Agency")
    _set_tenant_financials(db_session, tenant_id, False)
    expectation = _make_facility_expectation(db_session, tenant_id, mrn_prefix="OWN1")
    _set_tenant_billing_user(db_session, tenant_id=tenant_id)

    response = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("BILLING", tenant_id),
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["count"] >= 1
    assert any(item["id"] == str(expectation.id) for item in payload["items"])
    assert all(item["tenant_id"] == str(tenant_id) for item in payload["items"])


def test_platform_billing_user_with_active_scoped_assignment_can_access_facility_collections(
    client,
    db_session,
    tenant,
):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Assigned Agency")
    _set_tenant_financials(db_session, tenant_id, True)
    expectation = _make_facility_expectation(db_session, tenant_id, mrn_prefix="ASSIGN1")

    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _set_platform_billing_user(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=provider_tenant_id,
    )
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
        service_scopes=["FACILITY_COLLECTIONS"],
    )

    response = client.get(
        f"/billing/facility-payments/expectations/{expectation.id}",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
    )

    assert response.status_code == 200, response.text
    assert response.json()["tenant_id"] == str(tenant_id)


def test_platform_billing_user_without_assignment_cannot_access_facility_collections(
    client,
    db_session,
    tenant,
):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Unassigned Agency")
    _set_tenant_financials(db_session, tenant_id, True)
    _make_facility_expectation(db_session, tenant_id, mrn_prefix="NOASSIGN")

    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _set_platform_billing_user(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=provider_tenant_id,
    )

    response = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )

    assert response.status_code == 403


@pytest.mark.parametrize("relationship_status", ["SUSPENDED", "TERMINATED"])
def test_platform_billing_user_with_inactive_assignment_status_is_denied(
    client,
    db_session,
    tenant,
    relationship_status,
):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Inactive Relationship Agency")
    _set_tenant_financials(db_session, tenant_id, True)
    _make_facility_expectation(db_session, tenant_id, mrn_prefix="RELSTAT")

    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _set_platform_billing_user(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=provider_tenant_id,
    )
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
        relationship_status=relationship_status,
    )

    response = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    ("effective_start_at", "effective_end_at"),
    [
        (
            datetime.now(timezone.utc) + timedelta(days=1),
            None,
        ),
        (
            datetime.now(timezone.utc) - timedelta(days=10),
            datetime.now(timezone.utc) - timedelta(days=1),
        ),
    ],
)
def test_platform_billing_user_outside_assignment_effective_window_is_denied(
    client,
    db_session,
    tenant,
    effective_start_at,
    effective_end_at,
):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Expired Relationship Agency")
    _set_tenant_financials(db_session, tenant_id, True)
    _make_facility_expectation(db_session, tenant_id, mrn_prefix="WINDOW")

    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _set_platform_billing_user(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=provider_tenant_id,
    )
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
        effective_start_at=effective_start_at,
        effective_end_at=effective_end_at,
    )

    response = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )

    assert response.status_code == 403


def test_platform_billing_user_without_facility_collections_scope_is_denied(
    client,
    db_session,
    tenant,
):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Wrong Scope Agency")
    _set_tenant_financials(db_session, tenant_id, True)
    _make_facility_expectation(db_session, tenant_id, mrn_prefix="NOSCOPE")

    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _set_platform_billing_user(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=provider_tenant_id,
    )
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
        service_scopes=["PAYMENT_POSTING"],
    )

    response = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )

    assert response.status_code == 403


def test_platform_billing_user_is_denied_when_tenant_financials_are_off(
    client,
    db_session,
    tenant,
):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Tenant Financials Off Agency")
    _set_tenant_financials(db_session, tenant_id, False)
    _make_facility_expectation(db_session, tenant_id, mrn_prefix="TENOFF")

    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _set_platform_billing_user(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=provider_tenant_id,
    )
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
        service_scopes=["FACILITY_COLLECTIONS"],
    )

    response = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )

    assert response.status_code == 403


def test_platform_billing_user_is_denied_when_assignment_financials_are_off(
    client,
    db_session,
    tenant,
):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Assignment Financials Off Agency")
    _set_tenant_financials(db_session, tenant_id, True)
    _make_facility_expectation(db_session, tenant_id, mrn_prefix="ASSIGNOFF")

    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _set_platform_billing_user(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=provider_tenant_id,
    )
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
        assignment_financials_enabled=False,
    )

    response = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )

    assert response.status_code == 403


def test_platform_billing_all_agencies_returns_only_assigned_tenant_data(
    client,
    db_session,
    tenant,
):
    tenant_a = uuid.UUID(str(tenant.id))
    tenant_b = uuid.uuid4()
    _enable_billing_for_tenant(db_session, tenant_a, legal_name="Assigned Facility Agency")
    _enable_billing_for_tenant(db_session, tenant_b, legal_name="Unassigned Facility Agency")
    _set_tenant_financials(db_session, tenant_a, True)
    _set_tenant_financials(db_session, tenant_b, True)
    expectation_a = _make_facility_expectation(db_session, tenant_a, mrn_prefix="AGA")
    _make_facility_expectation(db_session, tenant_b, mrn_prefix="AGB")

    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _set_platform_billing_user(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=provider_tenant_id,
    )
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_a,
        service_scopes=["FACILITY_COLLECTIONS"],
    )

    response = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"all_agencies": "true"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["count"] == 1
    assert payload["items"][0]["id"] == str(expectation_a.id)
    assert {item["tenant_id"] for item in payload["items"]} == {str(tenant_a)}


def test_cross_tenant_expectation_detail_request_returns_404_for_unassigned_provider_user(
    client,
    db_session,
):
    assigned_tenant = uuid.uuid4()
    unassigned_tenant = uuid.uuid4()
    _enable_billing_for_tenant(db_session, assigned_tenant, legal_name="Assigned Detail Agency")
    _enable_billing_for_tenant(db_session, unassigned_tenant, legal_name="Unassigned Detail Agency")
    _set_tenant_financials(db_session, assigned_tenant, True)
    _set_tenant_financials(db_session, unassigned_tenant, True)
    provider_org_id = _make_billing_provider_organization(db_session).id
    _create_assignment(
        db_session,
        provider_org_id=provider_org_id,
        tenant_id=assigned_tenant,
        service_scopes=["FACILITY_COLLECTIONS"],
    )
    provider_tenant_id = _make_provider_tenant(db_session)
    _set_platform_billing_user(
        db_session,
        provider_org_id=provider_org_id,
        tenant_id=provider_tenant_id,
    )
    expectation = _make_facility_expectation(db_session, unassigned_tenant, mrn_prefix="XOBJ")

    response = client.get(
        f"/billing/facility-payments/expectations/{expectation.id}",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
    )

    assert response.status_code == 404


def test_platform_billing_all_agencies_without_assignments_returns_empty_list(
    client,
    db_session,
):
    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _set_platform_billing_user(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=provider_tenant_id,
    )

    response = client.get(
        "/billing/facility-payments/expectations",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"all_agencies": "true"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["items"] == []


def test_authorized_scopes_also_gate_aging_credit_balance_and_payment_posting(
    client,
    db_session,
    tenant,
):
    tenant_id = uuid.UUID(str(tenant.id))
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="Cross Router Agency")
    _set_tenant_financials(db_session, tenant_id, True)

    cycle = _make_billing_cycle(db_session, tenant_id, month=4)
    patient = _make_patient(db_session, tenant_id, mrn_prefix="ROUTER")
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
    _make_payment(
        db_session,
        tenant_id=tenant_id,
        remittance_advice_id=remittance.id,
        claim_id=claim.id,
        paid_amount=Decimal("150.00"),
    )

    provider_org = _make_billing_provider_organization(db_session)
    provider_tenant_id = _make_provider_tenant(db_session)
    _set_platform_billing_user(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=provider_tenant_id,
    )
    _create_assignment(
        db_session,
        provider_org_id=provider_org.id,
        tenant_id=tenant_id,
        service_scopes=[
            "FACILITY_COLLECTIONS",
            "FINANCIAL_MONITORING",
            "PAYMENT_RECONCILIATION",
            "PAYMENT_POSTING",
        ],
    )

    aging = client.get(
        "/billing/aging-report",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )
    credit = client.get(
        "/billing/credit-balance/report",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )
    remittances = client.get(
        "/billing/remittances",
        headers=_headers("PLATFORM_BILLING", provider_tenant_id),
        params={"tenant_id": str(tenant_id)},
    )

    assert aging.status_code == 200, aging.text
    assert credit.status_code == 200, credit.text
    assert remittances.status_code == 200, remittances.text
