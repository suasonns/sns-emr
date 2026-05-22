# tests/services/test_dx_policy.py

from uuid import UUID

from app.services.dx_policy import evaluate_primary_dx_policy


def test_f_code_blocked_as_primary(db_session, tenant):
    allowed, reason = evaluate_primary_dx_policy(
        db=db_session,
        tenant_id=tenant.id,
        icd10_code="F03.90",
    )

    assert allowed is False
    assert reason is not None
    assert "not allowed" in reason.lower()


def test_r_code_blocked_as_primary(db_session, tenant):
    allowed, _ = evaluate_primary_dx_policy(
        db=db_session,
        tenant_id=tenant.id,
        icd10_code="R64",
    )

    assert allowed is False


def test_z_code_blocked_as_primary(db_session, tenant):
    allowed, _ = evaluate_primary_dx_policy(
        db=db_session,
        tenant_id=tenant.id,
        icd10_code="Z99.89",
    )

    assert allowed is False


def test_valid_primary_dx_allowed(db_session, tenant):
    allowed, reason = evaluate_primary_dx_policy(
        db=db_session,
        tenant_id=tenant.id,
        icd10_code="I50.9",
    )

    assert allowed is True
    assert reason is None


def test_empty_icd_is_allowed(db_session, tenant):
    allowed, reason = evaluate_primary_dx_policy(
        db=db_session,
        tenant_id=tenant.id,
        icd10_code="",
    )

    assert allowed is True
    assert reason is None