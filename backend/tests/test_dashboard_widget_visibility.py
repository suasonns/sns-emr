"""Role-by-role coverage for the dashboard compliance-queue widget-visibility
engine (app.services.dashboard_service).

These tests exist to prove the authority-separation model holds:
  - An unmapped/unknown role is denied by default (no widgets at all).
  - Provider-signature authority (md_signatures_pending) is never granted to
    field RN/LVN staff, who instead get the coordination-only
    orders_requiring_clinical_action widget over the same underlying data.
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
            {"key": "md_signatures_pending", "label": "MD Signatures Pending", "value": 3, "tone": "red"},
            {"key": "cti_due_missing", "label": "CTI Due / Missing", "value": 1, "tone": "red"},
            {"key": "hope_due", "label": "HOPE Due", "value": None, "tone": "red", "data_available": False},
            {"key": "qies_rejected", "label": "QIES Rejected", "value": None, "tone": "red", "data_available": False},
        ],
        "priority_2": [
            {"key": "orders_requiring_clinical_action", "label": "Orders Requiring Clinical Action", "value": 3, "tone": "orange"},
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


def test_administrator_sees_agency_wide_widgets():
    filtered = _filter_widgets_for_role(_sample_queue(), "ADMINISTRATOR")
    keys = _keys(filtered)
    assert "hope_due" in keys
    assert "qies_rejected" in keys
    assert "admissions_pipeline" in keys
    assert "referrals" in keys
    assert "md_signatures_pending" in keys
    # Administrator does not perform RN coordination follow-up.
    assert "orders_requiring_clinical_action" not in keys


def test_rn_gets_coordination_widget_not_signature_widget():
    filtered = _filter_widgets_for_role(_sample_queue(), "RN")
    keys = _keys(filtered)
    assert "orders_requiring_clinical_action" in keys
    assert "md_signatures_pending" not in keys, (
        "RN must never see the physician signature-authority widget — "
        "coordinating an order is not the same authority as signing it."
    )
    # Field clinicians never see agency-wide compliance rollups.
    assert "hope_due" not in keys
    assert "qies_rejected" not in keys
    assert "admissions_pipeline" not in keys
    assert "referrals" not in keys


def test_lvn_gets_coordination_widget_not_signature_widget():
    filtered = _filter_widgets_for_role(_sample_queue(), "LVN")
    keys = _keys(filtered)
    assert "orders_requiring_clinical_action" in keys
    assert "md_signatures_pending" not in keys


def test_medical_director_sees_signature_widget_not_coordination_widget():
    filtered = _filter_widgets_for_role(_sample_queue(), "MEDICAL_DIRECTOR")
    keys = _keys(filtered)
    assert "md_signatures_pending" in keys
    assert "orders_requiring_clinical_action" not in keys


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
        assert "md_signatures_pending" not in keys
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


def test_compliance_officer_sees_agency_wide_monitoring_but_not_signature_or_coordination():
    """COMPLIANCE_OFFICER/QA_MANAGER/QA_REVIEWER hold agency-wide monitoring
    authority (CMS/CDPH survey-readiness, documentation accountability) —
    the same agency-wide widgets as ADMINISTRATOR/DPCS — but never
    physician signature authority, never RN/LVN coordination duty, and
    never Intake's admissions/referral pipeline (a distinct authority)."""
    for role in ("COMPLIANCE_OFFICER", "QA_MANAGER", "QA_REVIEWER"):
        keys = _keys(_filter_widgets_for_role(_sample_queue(), role))
        assert "hope_due" in keys
        assert "qies_rejected" in keys
        assert "cti_due_missing" in keys
        assert "rnica_incomplete" in keys
        assert "idg_blockers" in keys
        assert "md_signatures_pending" not in keys, (
            f"{role} monitors compliance but must never hold signature authority."
        )
        assert "orders_requiring_clinical_action" not in keys, (
            f"{role} must never hold RN/LVN care-coordination duty."
        )
        assert "admissions_pipeline" not in keys
        assert "referrals" not in keys


def test_intake_roles_see_pipeline_but_not_clinical_signature_widgets():
    for role in ("INTAKE_MANAGER", "INTAKE_COORDINATOR"):
        keys = _keys(_filter_widgets_for_role(_sample_queue(), role))
        assert "admissions_pipeline" in keys
        assert "referrals" in keys
        assert "md_signatures_pending" not in keys
        assert "hope_due" not in keys


def test_same_api_shape_different_users_different_keys():
    """Same queue payload, different role => different authorized widget
    keys — the core proof this is backend-enforced, not a frontend hide."""
    admin_keys = _keys(_filter_widgets_for_role(_sample_queue(), "ADMINISTRATOR"))
    rn_keys = _keys(_filter_widgets_for_role(_sample_queue(), "RN"))
    unknown_keys = _keys(_filter_widgets_for_role(_sample_queue(), "NOT_A_REAL_ROLE"))

    assert admin_keys != rn_keys
    assert unknown_keys == set()
    assert unknown_keys != admin_keys
    assert unknown_keys != rn_keys
