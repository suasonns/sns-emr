"""Role-by-role coverage for the dashboard compliance-queue widget-visibility
engine (app.services.dashboard_service).

These tests exist to prove the authority-separation model holds:
  - An unmapped/unknown role is denied by default (no widgets at all).
  - The physician-signature queue is split into three distinct authorities:
      * md_signatures_pending_oversight — view/monitor only (Administrator,
        DPCS, DPCS_ADMINISTRATOR, Clinical Supervisor, Compliance/QA).
      * orders_requiring_my_signature — the actual credentialed signer
        (Medical Director, Attending Physician) only.
      * orders_requiring_clinical_follow_up — RN/LVN/DPCS/Clinical
        Supervisor coordination duty, never a signature action.
    Holding the oversight/monitoring widget must never imply holding the
    signature widget, and vice versa.
  - Agency-wide compliance widgets (HOPE/QIES) are never granted to
    field-clinician roles.
  - DPCS_ADMINISTRATOR (an agency principal holding both titles) sees the
    union of ADMINISTRATOR + DPCS widgets, including referral/admissions
    pipeline metrics that a plain DPCS does not.
"""

from __future__ import annotations

from app.services.dashboard_service import (
    CANONICAL_DASHBOARD_ROLES,
    WIDGET_VISIBILITY,
    _filter_widgets_for_role,
)


def _sample_queue() -> dict:
    return {
        "priority_1": [
            {"key": "md_signatures_pending_oversight", "label": "MD Signatures Pending", "value": 3, "tone": "red", "action_label": "Review Queue"},
            {"key": "orders_requiring_my_signature", "label": "Orders Requiring My Signature", "value": 3, "tone": "red", "action_label": "Review and Sign"},
            {"key": "cti_due_missing", "label": "CTI Due / Missing", "value": 1, "tone": "red"},
            {"key": "hope_due", "label": "HOPE Due", "value": None, "tone": "red", "data_available": False},
            {"key": "qies_rejected", "label": "QIES Rejected", "value": None, "tone": "red", "data_available": False},
        ],
        "priority_2": [
            {"key": "orders_requiring_clinical_follow_up", "label": "Orders Requiring Clinical Follow-up", "value": 3, "tone": "orange", "action_label": "Open Follow-up"},
            {"key": "rnica_incomplete", "label": "RNICA Incomplete", "value": 2, "tone": "orange"},
            {"key": "idg_blockers", "label": "IDG Blockers", "value": 1, "tone": "orange"},
        ],
        "priority_3": [
            {"key": "admissions_pipeline", "label": "Admissions Pipeline", "value": 5, "tone": "blue"},
            {"key": "referrals", "label": "Referrals", "value": 2, "tone": "blue"},
        ],
    }


def _keys(filtered: dict) -> set[str]:
    return {item["key"] for items in filtered.values() for item in items}


def test_unknown_role_is_denied_by_default():
    filtered = _filter_widgets_for_role(_sample_queue(), "SOME_FUTURE_ROLE_NOT_YET_MAPPED")
    assert _keys(filtered) == set()
    for items in filtered.values():
        assert items == []


def test_missing_role_is_denied_by_default():
    filtered = _filter_widgets_for_role(_sample_queue(), None)
    assert _keys(filtered) == set()


def test_administrator_monitors_but_cannot_sign():
    """Acceptance test 1: Administrator can review the MD-signature backlog
    but must never receive the actual signature widget."""
    filtered = _filter_widgets_for_role(_sample_queue(), "ADMINISTRATOR")
    keys = _keys(filtered)
    assert "hope_due" in keys
    assert "qies_rejected" in keys
    assert "admissions_pipeline" in keys
    assert "referrals" in keys
    assert "md_signatures_pending_oversight" in keys
    assert "orders_requiring_my_signature" not in keys, (
        "Administrator must never receive the actual signature widget."
    )
    # Administrator does not perform RN coordination follow-up.
    assert "orders_requiring_clinical_follow_up" not in keys


def test_dpcs_monitors_but_cannot_sign():
    """Acceptance test 2: DPCS can monitor the backlog but cannot sign
    unless separately credentialed. DPCS DOES hold clinical follow-up
    (coordination), which is distinct from signing."""
    filtered = _filter_widgets_for_role(_sample_queue(), "DPCS")
    keys = _keys(filtered)
    assert "md_signatures_pending_oversight" in keys
    assert "orders_requiring_my_signature" not in keys
    assert "orders_requiring_clinical_follow_up" in keys


def test_rn_gets_follow_up_widget_not_signature_widgets():
    filtered = _filter_widgets_for_role(_sample_queue(), "RN")
    keys = _keys(filtered)
    assert "orders_requiring_clinical_follow_up" in keys
    assert "orders_requiring_my_signature" not in keys, (
        "RN must never see the physician signature-authority widget — "
        "coordinating an order is not the same authority as signing it."
    )
    assert "md_signatures_pending_oversight" not in keys, (
        "RN is not an oversight role and should not see the agency backlog widget."
    )
    # Field clinicians never see agency-wide compliance rollups.
    assert "hope_due" not in keys
    assert "qies_rejected" not in keys
    assert "admissions_pipeline" not in keys
    assert "referrals" not in keys


def test_lvn_gets_follow_up_widget_not_signature_widgets():
    filtered = _filter_widgets_for_role(_sample_queue(), "LVN")
    keys = _keys(filtered)
    assert "orders_requiring_clinical_follow_up" in keys
    assert "orders_requiring_my_signature" not in keys
    assert "md_signatures_pending_oversight" not in keys


def test_medical_director_sees_signature_widget_only():
    """Acceptance test 4: Medical Director sees "Orders Requiring My
    Signature" and only performs authorized signature actions — never the
    oversight-only widget or the RN/LVN coordination widget."""
    filtered = _filter_widgets_for_role(_sample_queue(), "MEDICAL_DIRECTOR")
    keys = _keys(filtered)
    assert "orders_requiring_my_signature" in keys
    assert "md_signatures_pending_oversight" not in keys
    assert "orders_requiring_clinical_follow_up" not in keys


def test_attending_physician_sees_signature_widget_only():
    """Acceptance test 5: Attending Physician sees only the signature
    widget (not oversight or coordination). NOTE: true per-patient scoping
    to the physician's own patients is not yet implemented — see
    SIGNATURE_SCOPING_NOT_YET_IMPLEMENTED in dashboard_service.py — this
    test covers widget-key authority only."""
    filtered = _filter_widgets_for_role(_sample_queue(), "ATTENDING_PHYSICIAN")
    keys = _keys(filtered)
    assert "orders_requiring_my_signature" in keys
    assert "md_signatures_pending_oversight" not in keys
    assert "orders_requiring_clinical_follow_up" not in keys


def test_dpcs_administrator_is_union_of_dpcs_and_administrator():
    dpcs_keys = _keys(_filter_widgets_for_role(_sample_queue(), "DPCS"))
    dpcs_admin_keys = _keys(_filter_widgets_for_role(_sample_queue(), "DPCS_ADMINISTRATOR"))
    admin_keys = _keys(_filter_widgets_for_role(_sample_queue(), "ADMINISTRATOR"))

    # DPCS alone does not get referral/admissions pipeline metrics.
    assert "referrals" not in dpcs_keys
    assert "admissions_pipeline" not in dpcs_keys

    # DPCS_ADMINISTRATOR holds both titles and gets the union.
    assert dpcs_keys <= dpcs_admin_keys
    assert "referrals" in dpcs_admin_keys
    assert "admissions_pipeline" in dpcs_admin_keys
    assert dpcs_admin_keys <= admin_keys | dpcs_keys


def test_msw_and_chaplain_never_see_signature_or_agency_widgets():
    for role in ("SW", "CHAPLAIN"):
        keys = _keys(_filter_widgets_for_role(_sample_queue(), role))
        assert "md_signatures_pending_oversight" not in keys
        assert "orders_requiring_my_signature" not in keys
        assert "hope_due" not in keys
        assert "qies_rejected" not in keys
        assert "admissions_pipeline" not in keys
        assert "referrals" not in keys


def test_every_canonical_role_has_been_deliberately_considered():
    """Every widget's visibility set must only reference roles that are
    part of the canonical role list — guards against typos silently
    creating an unreachable or over-broad rule."""
    for widget_key, roles in WIDGET_VISIBILITY.items():
        unknown = roles - CANONICAL_DASHBOARD_ROLES
        assert not unknown, f"{widget_key} references unmapped roles: {unknown}"


def test_compliance_officer_monitors_but_cannot_sign_or_coordinate():
    """Acceptance test 3: COMPLIANCE_OFFICER/QA_MANAGER/QA_REVIEWER hold
    agency-wide monitoring authority (CMS/CDPH survey-readiness,
    documentation accountability) — the same agency-wide widgets as
    ADMINISTRATOR/DPCS, plus the oversight-only signature-backlog widget —
    but never actual signature authority and never RN/LVN coordination
    duty, and never Intake's admissions/referral pipeline."""
    for role in ("COMPLIANCE_OFFICER", "QA_MANAGER", "QA_REVIEWER"):
        keys = _keys(_filter_widgets_for_role(_sample_queue(), role))
        assert "hope_due" in keys
        assert "qies_rejected" in keys
        assert "cti_due_missing" in keys
        assert "rnica_incomplete" in keys
        assert "idg_blockers" in keys
        assert "md_signatures_pending_oversight" in keys
        assert "orders_requiring_my_signature" not in keys, (
            f"{role} monitors compliance but must never hold signature authority."
        )
        assert "orders_requiring_clinical_follow_up" not in keys, (
            f"{role} must never hold RN/LVN care-coordination duty."
        )
        assert "admissions_pipeline" not in keys
        assert "referrals" not in keys


def test_intake_roles_see_pipeline_but_not_clinical_signature_widgets():
    for role in ("INTAKE_MANAGER", "INTAKE_COORDINATOR"):
        keys = _keys(_filter_widgets_for_role(_sample_queue(), role))
        assert "admissions_pipeline" in keys
        assert "referrals" in keys
        assert "md_signatures_pending_oversight" not in keys
        assert "orders_requiring_my_signature" not in keys
        assert "hope_due" not in keys


def test_unknown_role_receives_no_protected_signature_widgets():
    """Acceptance test 7: unknown role receives no protected dashboard data,
    including all three signature/follow-up widget keys."""
    keys = _keys(_filter_widgets_for_role(_sample_queue(), "TOTALLY_UNKNOWN_ROLE"))
    assert keys == set()


def test_same_api_shape_different_users_different_keys():
    """Same queue payload, different role => different authorized widget
    keys — the core proof this is backend-enforced, not a frontend hide."""
    admin_keys = _keys(_filter_widgets_for_role(_sample_queue(), "ADMINISTRATOR"))
    rn_keys = _keys(_filter_widgets_for_role(_sample_queue(), "RN"))
    md_keys = _keys(_filter_widgets_for_role(_sample_queue(), "MEDICAL_DIRECTOR"))
    unknown_keys = _keys(_filter_widgets_for_role(_sample_queue(), "NOT_A_REAL_ROLE"))

    assert admin_keys != rn_keys != md_keys
    assert unknown_keys == set()
    assert unknown_keys != admin_keys
    assert unknown_keys != rn_keys
    assert unknown_keys != md_keys
