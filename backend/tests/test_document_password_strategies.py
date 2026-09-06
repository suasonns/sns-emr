from __future__ import annotations

import uuid

from app.services.document_password_strategies import get_configured_password_candidates


def test_returns_empty_list_when_unconfigured(monkeypatch):
    monkeypatch.delenv("DOCUMENT_PASSWORD_STRATEGIES_JSON", raising=False)
    assert get_configured_password_candidates(uuid.uuid4()) == []


def test_returns_empty_list_on_invalid_json(monkeypatch):
    monkeypatch.setenv("DOCUMENT_PASSWORD_STRATEGIES_JSON", "not valid json")
    assert get_configured_password_candidates(uuid.uuid4()) == []


def test_returns_empty_list_when_tenant_not_present(monkeypatch):
    tenant_id = uuid.uuid4()
    monkeypatch.setenv(
        "DOCUMENT_PASSWORD_STRATEGIES_JSON",
        f'{{"{uuid.uuid4()}": ["some-password"]}}',
    )
    assert get_configured_password_candidates(tenant_id) == []


def test_returns_configured_candidates_for_tenant(monkeypatch):
    tenant_id = uuid.uuid4()
    monkeypatch.setenv(
        "DOCUMENT_PASSWORD_STRATEGIES_JSON",
        f'{{"{tenant_id}": ["candidate-one", "candidate-two"]}}',
    )
    assert get_configured_password_candidates(tenant_id) == ["candidate-one", "candidate-two"]


def test_ignores_non_string_entries(monkeypatch):
    tenant_id = uuid.uuid4()
    monkeypatch.setenv(
        "DOCUMENT_PASSWORD_STRATEGIES_JSON",
        f'{{"{tenant_id}": ["valid", 123, null, ""]}}',
    )
    assert get_configured_password_candidates(tenant_id) == ["valid"]
