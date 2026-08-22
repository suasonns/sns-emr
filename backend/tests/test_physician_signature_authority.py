"""Authority-separation coverage for real physician-order signing.

Regression guard for a confirmed gap: `role_matches`'s clinical-admin
fallback (ADMINISTRATOR/DPCS/DPCS_ADMINISTRATOR satisfy any clinical gate)
allowed Administrator/DPCS accounts to call the MD-only order-approval and
IDG batch-signature endpoints, even though they hold no prescribing
authority. Dashboard *visibility* of a signature queue must never imply
*signing* capability — these tests prove the endpoints' authorization
(`require_roles(..., allow_clinical_admin=False)`), independent of the
dashboard widget engine, actually enforces that separation.
"""

from __future__ import annotations

from app.api.physician_orders import MD_ONLY as PHYSICIAN_ORDERS_MD_ONLY
from app.api.idg.router import MD_ONLY as IDG_MD_ONLY
from app.core.roles import role_matches


def _assert_only_prescribers_can_sign(md_only: list[str]) -> None:
    # Real prescriber roles (legacy "MD" plus the newer canonical roles) may sign.
    for role in ("MD", "MEDICAL_DIRECTOR", "ATTENDING_PHYSICIAN"):
        assert role_matches(role, md_only, allow_clinical_admin=False) is True

    # Administrative rank must NEVER satisfy a signature gate on its own.
    for role in ("ADMINISTRATOR", "DPCS", "DPCS_ADMINISTRATOR"):
        assert role_matches(role, md_only, allow_clinical_admin=False) is False

    # Field clinical/coordination roles cannot sign either.
    for role in ("RN", "LVN", "COMPLIANCE_OFFICER", "QA_MANAGER"):
        assert role_matches(role, md_only, allow_clinical_admin=False) is False

    # Unknown role is denied regardless.
    assert role_matches("BOGUS_ROLE", md_only, allow_clinical_admin=False) is False


def test_physician_order_approval_denies_administrative_rank():
    _assert_only_prescribers_can_sign(PHYSICIAN_ORDERS_MD_ONLY)


def test_idg_batch_signature_denies_administrative_rank():
    _assert_only_prescribers_can_sign(IDG_MD_ONLY)


def test_administrator_can_still_view_signature_queue_by_default():
    """Oversight roles may VIEW/MONITOR a signature queue (default gate
    behavior, allow_clinical_admin=True) even though they cannot sign it."""
    for role in ("ADMINISTRATOR", "DPCS", "DPCS_ADMINISTRATOR"):
        assert role_matches(role, PHYSICIAN_ORDERS_MD_ONLY) is True
        assert role_matches(role, IDG_MD_ONLY) is True
