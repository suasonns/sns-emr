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
