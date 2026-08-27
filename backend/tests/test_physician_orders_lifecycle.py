"""Physician Orders Phase 1 lifecycle expansion tests (owner directive
2026-08-21, additive-only): PENDING_CLINICAL_REVIEW / COMPLETED / EXPIRED,
conditional clinical review routing, transition validation, immutable
status-history audit trail, implementation vs. completion tracking, and
cancellation/expiration rules.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.patient import Patient
from app.services import physician_order_service as svc
from tests.conftest import TEST_USER_ID


def _make_patient(db_session, tenant_id):
    patient = Patient(
        tenant_id=tenant_id,
        mrn=f"TEST-{uuid.uuid4().hex[:8]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="C34.90",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.flush()
    return patient


def _make_draft(db_session, tenant_id, patient_id, **overrides):
    kwargs = dict(
        tenant_id=tenant_id,
        patient_id=patient_id,
        order_text="Increase morphine to 5mg q4h PRN",
        order_category="MEDICATION",
        source_type="VERBAL_PHONE",
        ordered_by_provider_name="Dr. Smith",
        ordered_by_provider_role="MD",
        ordered_at=datetime.now(timezone.utc),
        prescriber_authenticated=True,
        phone_readback_confirmed=True,
        created_by=TEST_USER_ID,
    )
    kwargs.update(overrides)
    return svc.create_draft(db_session, **kwargs)


class TestConditionalClinicalReview:
    def test_stat_priority_bypasses_review_requirement(self):
        assert svc.requires_clinical_review(
            entered_by_role="OFFICE_STAFF", priority="STAT",
            source_type="WRITTEN", prescriber_authenticated=False,
        ) is False

    def test_self_verifying_authenticated_role_skips_review(self):
        for role in ("MD", "NP", "PA", "RN"):
            assert svc.requires_clinical_review(
                entered_by_role=role, priority="ROUTINE",
                source_type="VERBAL_PHONE", prescriber_authenticated=True,
            ) is False

    def test_non_clinical_entry_requires_review(self):
        assert svc.requires_clinical_review(
            entered_by_role="OFFICE_STAFF", priority="ROUTINE",
            source_type="WRITTEN", prescriber_authenticated=True,
        ) is True

    def test_unauthenticated_entry_requires_review_even_for_rn(self):
        assert svc.requires_clinical_review(
            entered_by_role="RN", priority="ROUTINE",
            source_type="VERBAL_PHONE", prescriber_authenticated=False,
        ) is True


class TestSubmitRouting:
    def test_path_b_authorized_rn_skips_clinical_review(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = _make_draft(db_session, tenant_id, patient.id)

        order = svc.submit_for_approval(
            db_session, order=order, submitted_by=TEST_USER_ID, submitted_by_role="RN",
        )
        assert order.status == "PENDING_HOSPICE_MD_APPROVAL"
        assert order.clinical_review_required is False

    def test_path_a_office_entry_routes_to_clinical_review(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = _make_draft(db_session, tenant_id, patient.id)

        order = svc.submit_for_approval(
            db_session, order=order, submitted_by=TEST_USER_ID, submitted_by_role="OFFICE_STAFF",
        )
        assert order.status == "PENDING_CLINICAL_REVIEW"
        assert order.clinical_review_required is True

    def test_forced_bypass_of_a_required_review_needs_reason(self, db_session):
        """Office-staff entry of a ROUTINE order normally requires clinical
        review; forcing it to skip (force_clinical_review=False) without a
        bypass_reason must be rejected."""
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = _make_draft(db_session, tenant_id, patient.id)

        with pytest.raises(svc.PhysicianOrderError):
            svc.submit_for_approval(
                db_session, order=order, submitted_by=TEST_USER_ID, submitted_by_role="OFFICE_STAFF",
                force_clinical_review=False,
            )

        order = svc.submit_for_approval(
            db_session, order=order, submitted_by=TEST_USER_ID, submitted_by_role="OFFICE_STAFF",
            force_clinical_review=False, bypass_reason="STAT per attending, verified verbally",
        )
        assert order.status == "PENDING_HOSPICE_MD_APPROVAL"
        assert order.clinical_review_bypassed is True

    def test_stat_priority_never_requires_review_no_bypass_flag_set(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = _make_draft(db_session, tenant_id, patient.id, priority="STAT", urgency_reason="Uncontrolled pain")

        order = svc.submit_for_approval(
            db_session, order=order, submitted_by=TEST_USER_ID, submitted_by_role="OFFICE_STAFF",
        )
        assert order.status == "PENDING_HOSPICE_MD_APPROVAL"
        assert order.clinical_review_bypassed is False  # not "required-then-bypassed" — never required


class TestClinicalReviewCompletion:
    def test_approve_routes_to_md_approval(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = _make_draft(db_session, tenant_id, patient.id)
        order = svc.submit_for_approval(
            db_session, order=order, submitted_by=TEST_USER_ID, submitted_by_role="OFFICE_STAFF",
        )
        assert order.status == "PENDING_CLINICAL_REVIEW"

        order = svc.complete_clinical_review(
            db_session, order=order, reviewed_by=TEST_USER_ID, reviewed_by_role="RN", approve=True,
        )
        assert order.status == "PENDING_HOSPICE_MD_APPROVAL"
        assert order.clinical_review_result == "APPROVED_FOR_SIGNATURE"

    def test_return_to_draft_requires_reason(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = _make_draft(db_session, tenant_id, patient.id)
        order = svc.submit_for_approval(
            db_session, order=order, submitted_by=TEST_USER_ID, submitted_by_role="OFFICE_STAFF",
        )

        with pytest.raises(svc.PhysicianOrderError):
            svc.complete_clinical_review(
                db_session, order=order, reviewed_by=TEST_USER_ID, reviewed_by_role="RN", approve=False,
            )

        order = svc.complete_clinical_review(
            db_session, order=order, reviewed_by=TEST_USER_ID, reviewed_by_role="RN", approve=False,
            reason="Dosage unclear, needs clarification",
        )
        assert order.status == "DRAFT"
        assert order.clinical_review_result == "RETURNED_TO_DRAFT"


class TestImplementationVsCompletion:
    def _signed_order(self, db_session, tenant_id, patient_id):
        order = _make_draft(db_session, tenant_id, patient_id)
        order = svc.submit_for_approval(
            db_session, order=order, submitted_by=TEST_USER_ID, submitted_by_role="RN",
        )
        order = svc.approve_order(db_session, order=order, approved_by=TEST_USER_ID, approved_by_role="MD")
        return order

    def test_executed_is_distinct_from_completed(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = self._signed_order(db_session, tenant_id, patient.id)
        assert order.status == "APPROVED"

        order = svc.execute_order(db_session, order=order, executed_by=TEST_USER_ID, executed_by_role="RN")
        assert order.status == "EXECUTED"
        assert order.completed_at is None

        with pytest.raises(svc.PhysicianOrderError):
            svc.complete_order(db_session, order=order, completed_by=TEST_USER_ID, completion_evidence="")

        order = svc.complete_order(
            db_session, order=order, completed_by=TEST_USER_ID, completed_by_role="RN",
            completion_evidence="Medication administered per MAR; patient comfort confirmed at 1400.",
        )
        assert order.status == "COMPLETED"
        assert order.completed_at is not None
        assert order.completion_evidence


class TestExpirationAndCancellation:
    def test_expire_due_orders_preserves_signed_history(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = _make_draft(db_session, tenant_id, patient.id)
        order = svc.submit_for_approval(db_session, order=order, submitted_by=TEST_USER_ID, submitted_by_role="RN")
        order = svc.approve_order(db_session, order=order, approved_by=TEST_USER_ID, approved_by_role="MD")
        order.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db_session.add(order)
        db_session.commit()

        expired = svc.expire_due_orders(db_session, tenant_id=tenant_id)
        assert len(expired) == 1
        assert expired[0].status == "EXPIRED"
        # Original signature is preserved, not erased.
        assert expired[0].signed_by_user_id == TEST_USER_ID
        assert expired[0].signed_at is not None

    def test_cancel_requires_reason(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = _make_draft(db_session, tenant_id, patient.id)

        with pytest.raises(svc.PhysicianOrderError):
            svc.cancel_order(db_session, order=order, cancelled_by=TEST_USER_ID, reason=None)

        order = svc.cancel_order(db_session, order=order, cancelled_by=TEST_USER_ID, reason="Duplicate entry")
        assert order.status == "CANCELLED"

    def test_cannot_cancel_terminal_status(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = _make_draft(db_session, tenant_id, patient.id)
        order = svc.cancel_order(db_session, order=order, cancelled_by=TEST_USER_ID, reason="Duplicate entry")

        with pytest.raises(svc.PhysicianOrderError):
            svc.cancel_order(db_session, order=order, cancelled_by=TEST_USER_ID, reason="Try again")


class TestStatusHistoryAuditTrail:
    def test_every_transition_is_recorded_immutably(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = _make_draft(db_session, tenant_id, patient.id)
        order = svc.submit_for_approval(db_session, order=order, submitted_by=TEST_USER_ID, submitted_by_role="RN")
        order = svc.approve_order(db_session, order=order, approved_by=TEST_USER_ID, approved_by_role="MD")

        history = svc.get_status_history(db_session, tenant_id=tenant_id, order_id=order.id)
        transitions = [(e.from_status, e.to_status) for e in history]
        assert (None, "DRAFT") in transitions
        assert ("DRAFT", "PENDING_HOSPICE_MD_APPROVAL") in transitions
        assert ("PENDING_HOSPICE_MD_APPROVAL", "APPROVED") in transitions
        # Every event has a recorded actor and label.
        for e in history:
            assert e.changed_at is not None
            assert svc.label_for(e.to_status) != ""


class TestDisplayLabelLayer:
    def test_labels_do_not_change_stored_literals(self):
        assert svc.label_for("PENDING_HOSPICE_MD_APPROVAL") == "Pending Physician Signature"
        assert svc.label_for("APPROVED") == "Signed"
        assert svc.label_for("EXECUTED") == "Implemented"
        assert svc.label_for("PENDING_CLINICAL_REVIEW") == "Pending Clinical Review"
        assert svc.label_for("COMPLETED") == "Completed"
        assert svc.label_for("EXPIRED") == "Expired"
        # Unknown status falls back to the raw literal, never raises.
        assert svc.label_for("SOMETHING_NEW") == "SOMETHING_NEW"


class TestProviderSignatureAuthorityModel:
    """Owner directive (2026-08-21): replace the flat MD-only signer
    assumption with a tiered Primary Signer / Alternate Authorized
    Provider Signer model. Primary providers (Attending Physician,
    Hospice Physician, Medical Director, Medical Director Designee, and
    the legacy "MD" literal) may always sign. Alternate authorized
    provider signers (NP/PA) may sign ONLY STAT/URGENT orders in an
    eligible category, and MUST supply an alternate_signer_reason. Never
    "is this a physician?" — always "is this provider authorized to sign
    THIS document under THIS workflow?".
    """

    def _submitted_order(self, db_session, tenant_id, patient_id, **overrides):
        order = _make_draft(db_session, tenant_id, patient_id, **overrides)
        return svc.submit_for_approval(
            db_session, order=order, submitted_by=TEST_USER_ID, submitted_by_role="RN",
        )

    @pytest.mark.parametrize(
        "role",
        ["MD", "MEDICAL_DIRECTOR", "ATTENDING_PHYSICIAN", "HOSPICE_PHYSICIAN", "MEDICAL_DIRECTOR_DESIGNEE"],
    )
    def test_primary_signers_may_sign_any_priority_and_category(self, db_session, role):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = self._submitted_order(db_session, tenant_id, patient.id, order_category="LAB", priority="ROUTINE")
        order = svc.approve_order(db_session, order=order, approved_by=TEST_USER_ID, approved_by_role=role)
        assert order.status == "APPROVED"
        assert order.signed_by_provider_role is not None
        assert order.alternate_signer_reason is None

    @pytest.mark.parametrize("role", ["NP", "PA"])
    def test_alternate_signer_authorized_for_stat_eligible_category(self, db_session, role):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = self._submitted_order(
            db_session, tenant_id, patient.id, order_category="MEDICATION",
            priority="STAT", urgency_reason="Uncontrolled dyspnea",
        )
        order = svc.approve_order(
            db_session, order=order, approved_by=TEST_USER_ID, approved_by_role=role,
            alternate_signer_reason="Attending Physician unreachable; patient in acute distress.",
        )
        assert order.status == "APPROVED"
        assert order.alternate_signer_reason

    @pytest.mark.parametrize("role", ["NP", "PA"])
    def test_alternate_signer_requires_reason(self, db_session, role):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = self._submitted_order(
            db_session, tenant_id, patient.id, order_category="MEDICATION",
            priority="STAT", urgency_reason="Uncontrolled dyspnea",
        )
        with pytest.raises(svc.PhysicianOrderError):
            svc.approve_order(db_session, order=order, approved_by=TEST_USER_ID, approved_by_role=role)

    @pytest.mark.parametrize("role", ["NP", "PA"])
    def test_alternate_signer_rejected_for_routine_order(self, db_session, role):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = self._submitted_order(db_session, tenant_id, patient.id, order_category="MEDICATION", priority="ROUTINE")
        with pytest.raises(svc.PhysicianOrderError):
            svc.approve_order(
                db_session, order=order, approved_by=TEST_USER_ID, approved_by_role=role,
                alternate_signer_reason="Not actually urgent",
            )

    @pytest.mark.parametrize("category", ["LAB", "DIET", "OTHER"])
    def test_alternate_signer_rejected_for_ineligible_category_even_if_stat(self, db_session, category):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = self._submitted_order(
            db_session, tenant_id, patient.id, order_category=category,
            priority="STAT", urgency_reason="Testing ineligible category",
        )
        with pytest.raises(svc.PhysicianOrderError):
            svc.approve_order(
                db_session, order=order, approved_by=TEST_USER_ID, approved_by_role="NP",
                alternate_signer_reason="Attempting to sign an ineligible-category STAT order",
            )

    @pytest.mark.parametrize("role", ["ADMINISTRATOR", "DPCS", "RN", "LVN"])
    def test_non_provider_roles_never_authorized_regardless_of_priority(self, db_session, role):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = self._submitted_order(
            db_session, tenant_id, patient.id, order_category="MEDICATION",
            priority="STAT", urgency_reason="Testing non-provider rejection",
        )
        with pytest.raises(svc.PhysicianOrderError):
            svc.approve_order(db_session, order=order, approved_by=TEST_USER_ID, approved_by_role=role)

    def test_signed_by_provider_role_recorded_for_primary_signer(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = self._submitted_order(db_session, tenant_id, patient.id)
        order = svc.approve_order(
            db_session, order=order, approved_by=TEST_USER_ID, approved_by_role="MEDICAL_DIRECTOR",
        )
        assert order.signed_by_provider_role == "MEDICAL_DIRECTOR"


class TestOrderedByProviderRoleContract:
    """Contract test: `ordered_by_provider_role` must accept every value in
    ``VALID_PROVIDER_ROLES`` (the single source of truth for this field, enforced
    in ``physician_order_service.create_draft``) and round-trip it through the
    `physician_orders.ordered_by_provider_role VARCHAR(16)` column without
    truncation or silent substitution. Any value outside that set must be
    rejected, not stored under a different value.
    """

    @pytest.mark.parametrize("role", sorted(svc.VALID_PROVIDER_ROLES))
    def test_every_valid_provider_role_round_trips_without_truncation(self, db_session, role):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = _make_draft(db_session, tenant_id, patient.id, ordered_by_provider_role=role)
        db_session.flush()
        db_session.refresh(order)
        assert order.ordered_by_provider_role == role

    def test_invalid_provider_role_is_rejected_not_substituted(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        with pytest.raises(svc.PhysicianOrderError):
            _make_draft(
                db_session, tenant_id, patient.id,
                ordered_by_provider_role="ATTENDING_PHYSICIAN",
            )


class TestProviderRoleUiNormalizationAuditTrail:
    """UI normalization layer (sns-emr-frontend/src/utils/providerRoleNormalization.js)
    lets staff type natural terminology ("attending physician", "doctor",
    etc.) and resolves it to a canonical MD/NP/PA value client-side. This
    class proves the backend contract that makes that safe:

    - only the canonical value is ever validated/stored on the order
      (unchanged strict VALID_PROVIDER_ROLES contract)
    - the original free-text and how it was resolved are preserved as
      audit metadata, never as the authoritative role
    - a caller cannot use `ordered_by_provider_role_source` to smuggle an
      unauthorized canonical value past validation
    """

    def test_audit_metadata_captures_original_input_and_normalization_method(self, db_session):
        from sqlalchemy import text

        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = _make_draft(
            db_session, tenant_id, patient.id,
            ordered_by_provider_role="MD",
            ordered_by_provider_role_source={
                "original_input": "Attending Physician",
                "normalized_value": "MD",
                "normalization_method": "ui_alias",
            },
        )

        # Canonical, strict value is what's actually stored on the order.
        assert order.ordered_by_provider_role == "MD"

        rows = db_session.execute(
            text(
                "SELECT metadata FROM audit_logs WHERE entity_id = :entity_id "
                "AND action = 'PHYSICIAN_ORDER_STATUS_TRANSITION' "
                "ORDER BY created_at ASC LIMIT 1"
            ),
            {"entity_id": str(order.id)},
        ).fetchone()
        assert rows is not None
        metadata = rows[0]
        if isinstance(metadata, str):
            import json

            metadata = json.loads(metadata)
        source = metadata["ordered_by_provider_role_source"]
        assert source["original_input"] == "Attending Physician"
        assert source["normalized_value"] == "MD"
        assert source["normalization_method"] == "ui_alias"

    def test_role_source_metadata_cannot_bypass_strict_validation(self, db_session):
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)

        # Even if the UI-normalization payload claims a canonical value,
        # the actual `ordered_by_provider_role` argument is the only thing
        # validated -- an invalid role is still rejected outright.
        with pytest.raises(svc.PhysicianOrderError):
            _make_draft(
                db_session, tenant_id, patient.id,
                ordered_by_provider_role="ATTENDING_PHYSICIAN",
                ordered_by_provider_role_source={
                    "original_input": "attending physician",
                    "normalized_value": "MD",
                    "normalization_method": "ui_alias",
                },
            )

    def test_missing_role_source_metadata_is_tolerated(self, db_session):
        # Callers that don't pass ordered_by_provider_role_source (e.g. the
        # existing frontend/back-compat clients) must keep working exactly
        # as before -- this field is strictly additive.
        tenant_id = uuid.UUID(db_session.info["tenant_id"])
        patient = _make_patient(db_session, tenant_id)
        order = _make_draft(db_session, tenant_id, patient.id, ordered_by_provider_role="NP")
        assert order.ordered_by_provider_role == "NP"
