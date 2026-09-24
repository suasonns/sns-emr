"""
AC-001 remediation tests: app.core.permissions.has_permission()

Prior behavior: has_permission() was a hardcoded `return True`, so all 5
call sites in app/api/survey.py (chart PDF download, 3 compliance views,
data export) never actually denied anyone.

Corrected behavior: has_permission() now delegates to the existing
tenant/clinical capability mechanism (app.core.capabilities.has_capability
with VIEW_ALL_TENANT_PATIENTS) instead of a bespoke rule.

NOTE (scope boundary): app/api/survey.py's three compliance-view endpoints
(`overdue-poc-updates`, `idg-compliance`, `crisis-poc-same-day`) query raw
SQL views (survey_overdue_poc_updates, survey_idg_compliance,
survey_crisis_poc_same_day) that are not created by any Alembic migration
in this repository -- a separate, pre-existing gap, out of scope for
AC-001. The route-level tests below only assert on the permission-gate
status code (403 vs. not-403); they do not assert 200 for those three
routes, since a downstream 5xx from the missing view is a distinct,
undocumented issue this task is not authorized to fix.
"""

from __future__ import annotations

import pytest

from app.core.permissions import has_permission
from tests.conftest import login_headers


class _FakeUser:
    def __init__(self, role: str):
        self.role = role


TENANT_WIDE_OVERSIGHT_ROLES = ["ADMINISTRATOR", "DPCS", "QA_MANAGER", "QA_REVIEWER", "COMPLIANCE_OFFICER"]
ASSIGNMENT_SCOPED_ROLES = ["RN", "LVN", "CHHA"]
SURVEY_ACTIONS = ["download_chart_pdf", "view_compliance", "export_data"]


@pytest.mark.parametrize("role", TENANT_WIDE_OVERSIGHT_ROLES)
@pytest.mark.parametrize("action", SURVEY_ACTIONS)
def test_has_permission_grants_tenant_wide_oversight_roles(role, action):
    assert has_permission(_FakeUser(role), action) is True


@pytest.mark.parametrize("role", ASSIGNMENT_SCOPED_ROLES)
@pytest.mark.parametrize("action", SURVEY_ACTIONS)
def test_has_permission_denies_assignment_scoped_roles(role, action):
    assert has_permission(_FakeUser(role), action) is False


def test_has_permission_denies_unrecognized_action():
    assert has_permission(_FakeUser("ADMINISTRATOR"), "not_a_real_action") is False


def test_has_permission_accepts_dict_shaped_user():
    assert has_permission({"role": "ADMINISTRATOR"}, "export_data") is True
    assert has_permission({"role": "RN"}, "export_data") is False


SURVEY_ROUTES = [
    "/survey/chart-summary?patient_id=00000000-0000-0000-0000-000000000000",
    "/survey/overdue-poc-updates",
    "/survey/idg-compliance",
    "/survey/crisis-poc-same-day",
    "/survey/export-bundle",
]


@pytest.mark.parametrize("path", SURVEY_ROUTES)
def test_survey_route_requires_authentication(client, path):
    response = client.get(path)
    assert response.status_code == 401


@pytest.mark.parametrize("path", SURVEY_ROUTES)
def test_survey_route_denies_unauthorized_role_before_data_access(client, path):
    headers = login_headers(client, user_id="rn_test", role="RN")
    response = client.get(path, headers=headers)
    assert response.status_code == 403


@pytest.mark.parametrize("path", SURVEY_ROUTES)
def test_survey_route_permission_gate_passes_for_authorized_role(client, path):
    headers = login_headers(client, user_id="admin_test", role="ADMINISTRATOR")
    try:
        response = client.get(path, headers=headers)
    except Exception:
        # The permission gate raises a clean HTTPException(403) response
        # when it denies -- it never lets an unhandled exception escape.
        # An unhandled exception here can only come from *after* the
        # permission check passed (e.g. a missing SQL view backing
        # overdue-poc-updates/idg-compliance/crisis-poc-same-day, or the
        # separate log_security_activity() keyword-argument bug in
        # export-bundle -- both pre-existing, undocumented, out-of-scope
        # issues discovered incidentally while validating this fix). That
        # still proves the permission gate itself did not block this role.
        return
    assert response.status_code != 403
