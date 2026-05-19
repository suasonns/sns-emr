import pytest


@pytest.mark.core_rule("8")
def test_never_auto_finalize_roles(monkeypatch):
    """
    Core Rule:
    Certain roles are NEVER eligible for auto-finalize,
    even if env vars are misconfigured.
    """
    policy = pytest.importorskip(
        "services.documentation.finalization_policy"
    )

    monkeypatch.setenv("TENANT_ALLOW_AUTO_FINALIZE", "true")

    for role in ["BSW", "AIDE", "CHHA", "AUDIT", "NOTE_REVIEW", "IDG_AUDIT"]:
        monkeypatch.setenv(f"DOC_AUTO_FINALIZE_{role}", "true")
        assert policy.can_auto_finalize(role) is False