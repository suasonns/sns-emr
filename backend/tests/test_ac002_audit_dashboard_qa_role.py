"""
AC-002 remediation tests: app/api/audit_dashboard.py "QA" role gate.

Prior behavior: the /audit-dashboard/patients gate used
require_roles(["ADMIN", "DPCS", "QA"]). The literal role "QA" is not an
issued role (see app.core.roles QA_ROLES / _ALIASES) -- no real
QA_MANAGER/QA_REVIEWER/COMPLIANCE_OFFICER account could ever pass it.

Corrected behavior: the gate now uses the canonical issued QA role
constants already imported in that module (app.core.roles.QA_ROLES),
alongside the existing ADMIN/DPCS entries.
"""

from __future__ import annotations

import pathlib

import pytest

from app.api import audit_dashboard
from tests.conftest import login_headers

QA_ROLES_TO_TEST = ["QA_MANAGER", "QA_REVIEWER", "COMPLIANCE_OFFICER"]


def test_literal_qa_role_string_removed_from_gate():
    """Regression guard: the unmatchable literal "QA" role must not
    reappear in the /audit-dashboard/patients gate."""
    source = pathlib.Path(audit_dashboard.__file__).read_text()
    assert '"QA"' not in source


@pytest.mark.parametrize("role", QA_ROLES_TO_TEST)
def test_issued_qa_roles_pass_the_gate(client, db_session, role):
    headers = login_headers(client, user_id="qa_test", role=role)
    response = client.get("/audit-dashboard/patients", headers=headers)
    assert response.status_code != 403


@pytest.mark.parametrize("role", ["ADMINISTRATOR", "DPCS"])
def test_admin_and_dpcs_access_preserved(client, db_session, role):
    headers = login_headers(client, user_id="admin_test", role=role)
    response = client.get("/audit-dashboard/patients", headers=headers)
    assert response.status_code != 403


def test_unrelated_role_is_denied(client, db_session):
    headers = login_headers(client, user_id="rn_test", role="RN")
    response = client.get("/audit-dashboard/patients", headers=headers)
    assert response.status_code == 403


def test_unauthenticated_request_is_denied(client):
    response = client.get("/audit-dashboard/patients")
    assert response.status_code == 401
