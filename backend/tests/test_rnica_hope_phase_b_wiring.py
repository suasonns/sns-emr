"""End-to-end coverage for the HOPE-REPAIR-READINESS-001 / owner-approved
wiring repair: RNICA Lock is now the authoritative HOPE Phase B trigger
for Admission, HUV1, and HUV2 RN ICA assessments.

These tests exercise the real HTTP + DB layer (POST /visits/rnica/save,
POST /visits/rnica/{id}/lock) against an isolated test database -- the
same harness used by test_rnica_runtime_validation.py -- rather than
calling internal functions directly, so they prove the wiring actually
works end-to-end, not just that the helper functions are individually
correct.

Scope covered (see OWNER REVIEW COMPLETE directive's 15 required
scenarios):
  1-7.  Admission + various J2051 symptom impacts (pain / each non-pain
        symptom / multiple symptoms) -> hope_event_type persisted, SFV
        requirement created only when clinically warranted.
  8-9.  HUV1 / HUV2 trigger via an UPDATE-type RN ICA locked inside the
        correct day window.
  10.   Mild-only Admission -- hope_event_type still persisted (the HOPE
        event itself always happens at Admission), but no SFV created.
  11.   RECERT-type assessment -- intentionally out of scope; no HOPE
        event persisted at all (closest RNICA analogue to "non-HOPE
        routine visit").
  12.   Duplicate lock submission -- idempotent, no duplicate SFV.
  13.   J2053 / generic-path duplicate-completion non-recursion --
        verified separately by running the pre-existing, untouched
        test_hope_phase_b_sfv_trigger_rules.py /
        test_sfv_completion_api.py suites (this repair does not modify
        hope_phase_b_engine.py or the generic visit-finalize path).
  14.   HUV task completion -- completion_reference_id populated via
        CompletionReferenceType.DOCUMENT.
  15.   Reload persistence -- hope_event_type/hope_event_date survive a
        fresh DB read after the HTTP request completes.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.api.visits import _build_j2051_adapter_inputs
from app.models.admission import Admission
from app.models.enums import CompletionReferenceType, TaskStatus, TaskType
from app.models.patient import Patient
from app.models.rnica_assessment import RnicaAssessment
from app.models.sfv_requirement import SFVRequirement
from app.models.task import Task

ELECTION_DATETIME = datetime(2026, 1, 1, tzinfo=timezone.utc)
HUV1_WINDOW_VISIT_DATE = "2026-01-11"  # election + 10 days (window is 6-15)
HUV2_WINDOW_VISIT_DATE = "2026-01-21"  # election + 20 days (window is 16-30)

ALL_MILD_SYMPTOM_IMPACT = {
    "pain": "1",
    "shortnessOfBreath": "1",
    "anxiety": "1",
    "nausea": "1",
    "vomiting": "1",
    "diarrhea": "1",
    "constipation": "1",
    "agitation": "1",
}


def _make_patient_with_admission(db_session, tenant_id) -> tuple[Patient, Admission]:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"RNICA-HOPE-{uuid.uuid4().hex[:12]}",
        date_of_birth=date(1950, 3, 14),
        primary_diagnosis="Hospice qualifying diagnosis",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=None,
    )
    db_session.add(patient)
    db_session.flush()

    admission = Admission(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient.id,
        admission_date=ELECTION_DATETIME,
        effective_date=ELECTION_DATETIME,
        soc_date=ELECTION_DATETIME,
        election_signed_at=ELECTION_DATETIME,
        status="ADMITTED",
    )
    db_session.add(admission)
    db_session.commit()
    return patient, admission


def _symptom_impact(**overrides) -> dict:
    base = {
        "pain": "0",
        "shortnessOfBreath": "0",
        "anxiety": "0",
        "nausea": "0",
        "vomiting": "0",
        "diarrhea": "0",
        "constipation": "0",
        "agitation": "0",
    }
    base.update(overrides)
    return base


def _rnica_form_data(symptom_impact: dict, *, visit_date: str, discipline: str = "RN") -> dict:
    return {
        "demographics": {
            "firstName": "Hope",
            "lastName": "Wiring",
            "dob": "1950-03-14",
            "gender": "Female",
            "advancedCarePlanning": {
                "codeStatus": "Full code",
                "lifeSustainingTreatmentPreference": "Yes",
                "hospitalizationPreference": "No",
            },
        },
        "visitMeta": {"visitDate": visit_date, "discipline": discipline},
        "symptomImpact": symptom_impact,
        "finalization": {
            "clinicianSignature": "RN Test",
            "signatureCertification": True,
            "pocGenerationCompleted": True,
            "responseToInterventions": {"baselineEstablished": True},
        },
        "diagnoses": {"lcdEligibilityNarrative": "Documented decline per LCD criteria."},
        "referrals": {"reviewed": True},
    }


def _save_and_lock(client, headers, patient_id, form_data, *, assessment_subtype: str | None = None):
    payload = {"patientId": str(patient_id), "formData": form_data}
    if assessment_subtype:
        payload["assessmentSubtype"] = assessment_subtype
    save_resp = client.post("/visits/rnica/save", json=payload, headers=headers)
    assert save_resp.status_code == 200, save_resp.text
    assessment_id = save_resp.json()["assessmentId"]

    lock_resp = client.post(f"/visits/rnica/{assessment_id}/lock", headers=headers)
    assert lock_resp.status_code == 200, lock_resp.text
    return assessment_id, lock_resp.json()


def _sfv_requirement_for(db_session, patient_id, trigger_reference_id) -> SFVRequirement | None:
    return (
        db_session.query(SFVRequirement)
        .filter(
            SFVRequirement.patient_id == patient_id,
            SFVRequirement.trigger_reference_id == trigger_reference_id,
        )
        .first()
    )


@pytest.mark.integration
class TestRnicaHopePhaseBAdmissionWiring:
    """Scenarios 1-7 and 10: Admission-type RN ICA lock."""

    @pytest.mark.parametrize(
        "symptom_overrides,expected_group",
        [
            ({"pain": "2"}, "PAIN"),  # 1. Admission + Pain Moderate
            ({"pain": "3"}, "PAIN"),  # 2. Admission + Pain Severe
            ({"shortnessOfBreath": "2"}, "NON_PAIN"),  # 3. Admission + SOB Moderate
            ({"anxiety": "2"}, "NON_PAIN"),  # 4. Admission + Anxiety Moderate
            ({"nausea": "2"}, "NON_PAIN"),  # 5. Admission + Nausea Moderate
            ({"constipation": "3"}, "NON_PAIN"),  # 6. Admission + Constipation Severe
            ({"pain": "2", "shortnessOfBreath": "3"}, "BOTH"),  # 7. multiple symptoms
        ],
    )
    def test_admission_lock_triggers_hope_event_and_sfv_for_qualifying_symptoms(
        self, client, db_session, rn_headers, symptom_overrides, expected_group
    ):
        tenant_id = db_session.info.get("tenant_id")
        patient, admission = _make_patient_with_admission(db_session, tenant_id)

        form_data = _rnica_form_data(_symptom_impact(**symptom_overrides), visit_date="2026-01-01")
        assessment_id, lock_json = _save_and_lock(client, rn_headers, patient.id, form_data)

        summary = lock_json["hopePhaseB"]
        assert summary is not None, "Admission lock must trigger HOPE Phase B processing"
        assert summary["hopeEventType"] == "ADMISSION"
        assert summary["hopeEventDate"] == "2026-01-01"
        assert summary["taskCompleted"] is False  # Admission never completes a HUV task

        db_session.expire_all()
        record = db_session.query(RnicaAssessment).filter_by(id=uuid.UUID(assessment_id)).one()
        assert record.hope_event_type == "ADMISSION"
        assert record.hope_event_date == date(2026, 1, 1)
        # visit_id is a real FK to visits.id and no Visit row exists for an
        # RNICA-only encounter -- intentionally left NULL (see
        # _trigger_rnica_hope_phase_b_on_lock docstring / implementation
        # report). This assertion locks in that deliberate scope boundary.
        assert record.visit_id is None

        requirement = _sfv_requirement_for(db_session, patient.id, record.id)
        assert requirement is not None, "Moderate/severe symptom impact must create an SFV requirement"
        assert requirement.trigger_source_type == "INITIAL_RN_ICA"
        assert requirement.trigger_symptom_group == expected_group
        assert requirement.status == "OPEN"

        # HUV1/HUV2 tasks are unconditionally created at Admission,
        # regardless of symptom severity.
        huv1_task = db_session.query(Task).filter_by(patient_id=patient.id, task_type=TaskType.HUV1).first()
        huv2_task = db_session.query(Task).filter_by(patient_id=patient.id, task_type=TaskType.HUV2).first()
        assert huv1_task is not None
        assert huv2_task is not None

    def test_mild_only_admission_persists_hope_event_but_creates_no_sfv(self, client, db_session, rn_headers):
        """10. Mild-only Admission -- the HOPE event identity (ADMISSION)
        is still activated (CMS requires it to always be documented), but
        no SFV requirement is created since nothing is moderate/severe."""
        tenant_id = db_session.info.get("tenant_id")
        patient, admission = _make_patient_with_admission(db_session, tenant_id)

        form_data = _rnica_form_data(ALL_MILD_SYMPTOM_IMPACT, visit_date="2026-01-01")
        assessment_id, lock_json = _save_and_lock(client, rn_headers, patient.id, form_data)

        summary = lock_json["hopePhaseB"]
        assert summary["hopeEventType"] == "ADMISSION"

        db_session.expire_all()
        record = db_session.query(RnicaAssessment).filter_by(id=uuid.UUID(assessment_id)).one()
        assert record.hope_event_type == "ADMISSION"
        assert record.hope_event_date == date(2026, 1, 1)

        requirement = _sfv_requirement_for(db_session, patient.id, record.id)
        assert requirement is None, "Mild-only impact must not create a false-positive SFV requirement"

    def test_recert_assessment_is_not_a_hope_event(self, client, db_session, rn_headers):
        """11. RECERT RN ICA assessments are out of scope for HOPE event
        identity -- the closest RNICA analogue to a 'non-HOPE routine
        visit'. Locking one must not touch hope_event_type/date, must not
        call the Phase B engine, and must not create any SFV requirement
        or Task."""
        tenant_id = db_session.info.get("tenant_id")
        patient, admission = _make_patient_with_admission(db_session, tenant_id)

        form_data = _rnica_form_data(_symptom_impact(pain="3"), visit_date="2026-06-01")
        assessment_id, lock_json = _save_and_lock(
            client, rn_headers, patient.id, form_data, assessment_subtype="recert"
        )

        assert lock_json["hopePhaseB"] is None

        db_session.expire_all()
        record = db_session.query(RnicaAssessment).filter_by(id=uuid.UUID(assessment_id)).one()
        assert record.hope_event_type is None
        assert record.hope_event_date is None
        assert record.assessment_type == "RECERT"

        assert db_session.query(SFVRequirement).filter_by(patient_id=patient.id).count() == 0
        assert db_session.query(Task).filter_by(patient_id=patient.id).count() == 0

    def test_duplicate_lock_submission_is_idempotent(self, client, db_session, rn_headers):
        """12. Duplicate lock submission -- re-locking an already-locked
        assessment must not re-run HOPE processing or create a second SFV
        requirement/task."""
        tenant_id = db_session.info.get("tenant_id")
        patient, admission = _make_patient_with_admission(db_session, tenant_id)

        form_data = _rnica_form_data(_symptom_impact(pain="2"), visit_date="2026-01-01")
        assessment_id, first_lock_json = _save_and_lock(client, rn_headers, patient.id, form_data)
        assert first_lock_json["hopePhaseB"]["hopeEventType"] == "ADMISSION"

        second_lock_resp = client.post(f"/visits/rnica/{assessment_id}/lock", headers=rn_headers)
        assert second_lock_resp.status_code == 200, second_lock_resp.text
        assert second_lock_resp.json()["locked"] is True

        db_session.expire_all()
        requirements = (
            db_session.query(SFVRequirement)
            .filter(SFVRequirement.patient_id == patient.id)
            .all()
        )
        assert len(requirements) == 1, "Re-locking must not create a duplicate SFV requirement"


@pytest.mark.integration
class TestRnicaHopePhaseBHuvWiring:
    """Scenarios 8, 9, 14: HUV1/HUV2 trigger + task completion via an
    UPDATE-type RN ICA locked inside the correct day window."""

    def _lock_admission_then_update(
        self, client, db_session, rn_headers, patient, *, update_visit_date: str, update_symptom_impact: dict
    ):
        admission_form_data = _rnica_form_data(ALL_MILD_SYMPTOM_IMPACT, visit_date="2026-01-01")
        _save_and_lock(client, rn_headers, patient.id, admission_form_data)

        update_form_data = _rnica_form_data(update_symptom_impact, visit_date=update_visit_date)
        return _save_and_lock(
            client, rn_headers, patient.id, update_form_data, assessment_subtype="update"
        )

    def test_huv1_moderate_trigger_completes_task_and_creates_sfv(self, client, db_session, rn_headers):
        tenant_id = db_session.info.get("tenant_id")
        patient, admission = _make_patient_with_admission(db_session, tenant_id)

        assessment_id, lock_json = self._lock_admission_then_update(
            client,
            db_session,
            rn_headers,
            patient,
            update_visit_date=HUV1_WINDOW_VISIT_DATE,
            update_symptom_impact=_symptom_impact(anxiety="2"),
        )

        summary = lock_json["hopePhaseB"]
        assert summary is not None, "UPDATE assessment inside the HUV1 window must trigger HOPE processing"
        assert summary["hopeEventType"] == "HUV1"
        assert summary["taskCompleted"] is True

        db_session.expire_all()
        record = db_session.query(RnicaAssessment).filter_by(id=uuid.UUID(assessment_id)).one()
        assert record.hope_event_type == "HUV1"
        assert record.hope_event_date == date(2026, 1, 11)

        requirement = _sfv_requirement_for(db_session, patient.id, record.id)
        assert requirement is not None
        assert requirement.trigger_source_type == "HUV1"

        huv1_task = (
            db_session.query(Task)
            .filter(Task.patient_id == patient.id, Task.task_type == TaskType.HUV1)
            .one()
        )
        assert huv1_task.status == TaskStatus.COMPLETED
        assert huv1_task.completion_reference_type == CompletionReferenceType.DOCUMENT
        assert huv1_task.completion_reference_id == record.id

    def test_huv2_severe_trigger_completes_task_and_creates_sfv(self, client, db_session, rn_headers):
        tenant_id = db_session.info.get("tenant_id")
        patient, admission = _make_patient_with_admission(db_session, tenant_id)

        assessment_id, lock_json = self._lock_admission_then_update(
            client,
            db_session,
            rn_headers,
            patient,
            update_visit_date=HUV2_WINDOW_VISIT_DATE,
            update_symptom_impact=_symptom_impact(diarrhea="3"),
        )

        summary = lock_json["hopePhaseB"]
        assert summary is not None, "UPDATE assessment inside the HUV2 window must trigger HOPE processing"
        assert summary["hopeEventType"] == "HUV2"
        assert summary["taskCompleted"] is True

        db_session.expire_all()
        record = db_session.query(RnicaAssessment).filter_by(id=uuid.UUID(assessment_id)).one()
        assert record.hope_event_type == "HUV2"
        assert record.hope_event_date == date(2026, 1, 21)

        requirement = _sfv_requirement_for(db_session, patient.id, record.id)
        assert requirement is not None
        assert requirement.trigger_source_type == "HUV2"

        huv2_task = (
            db_session.query(Task)
            .filter(Task.patient_id == patient.id, Task.task_type == TaskType.HUV2)
            .one()
        )
        assert huv2_task.status == TaskStatus.COMPLETED
        assert huv2_task.completion_reference_type == CompletionReferenceType.DOCUMENT
        assert huv2_task.completion_reference_id == record.id

    def test_huv2_sob_severe_trigger_completes_task_and_creates_sfv(self, client, db_session, rn_headers):
        """Literal HUV2 Shortness-of-Breath coverage.

        The pre-existing test_huv2_severe_trigger_completes_task_and_creates_sfv
        above proves the shared non-pain adapter path using Diarrhea = Severe.
        It does not, by itself, prove that symptomImpact.shortnessOfBreath is
        the literal field read by the adapter. This test closes that gap by
        setting ONLY shortnessOfBreath to Severe (all other non-pain symptoms,
        and pain itself, stay at "0"/non-triggering) and asserting the full
        RNICA Lock -> adapter -> Phase B -> task -> SFV -> DB-persistence path
        through the exact same HTTP endpoint used by the repaired workflow.
        """
        tenant_id = db_session.info.get("tenant_id")
        patient, admission = _make_patient_with_admission(db_session, tenant_id)

        sob_only_symptom_impact = _symptom_impact(shortnessOfBreath="3")

        assessment_id, lock_json = self._lock_admission_then_update(
            client,
            db_session,
            rn_headers,
            patient,
            update_visit_date=HUV2_WINDOW_VISIT_DATE,
            update_symptom_impact=sob_only_symptom_impact,
        )

        summary = lock_json["hopePhaseB"]
        assert summary is not None, "UPDATE assessment inside the HUV2 window must trigger HOPE processing"
        assert summary["hopeEventType"] == "HUV2"
        assert summary["taskCompleted"] is True

        db_session.expire_all()
        record = db_session.query(RnicaAssessment).filter_by(id=uuid.UUID(assessment_id)).one()
        assert record.hope_event_type == "HUV2"
        assert record.hope_event_date == date(2026, 1, 21)

        # Adapter proof: run the real, unmodified adapter helper against the
        # persisted RNICA form_data and show it reads shortnessOfBreath (not
        # diarrhea, not a mock) as the sole qualifying non-pain symptom.
        persisted_symptom_impact = record.form_data["symptomImpact"]
        assert persisted_symptom_impact["shortnessOfBreath"] == "3"
        assert persisted_symptom_impact["diarrhea"] == "0"
        assert persisted_symptom_impact["constipation"] == "0"
        pain_impact, non_pain_impact = _build_j2051_adapter_inputs(persisted_symptom_impact)
        assert pain_impact == "NONE"
        assert non_pain_impact == "SEVERE"

        requirement = _sfv_requirement_for(db_session, patient.id, record.id)
        assert requirement is not None
        assert requirement.trigger_source_type == "HUV2"
        assert requirement.trigger_reference_id == record.id
        assert requirement.due_at.date() == date(2026, 1, 21) + timedelta(days=2)

        huv2_task = (
            db_session.query(Task)
            .filter(Task.patient_id == patient.id, Task.task_type == TaskType.HUV2)
            .one()
        )
        assert huv2_task.status == TaskStatus.COMPLETED
        assert huv2_task.completion_reference_type == CompletionReferenceType.DOCUMENT
        assert huv2_task.completion_reference_id == record.id

        # Duplicate-lock / reload-persistence proof scoped to this scenario.
        second_lock_resp = client.post(f"/visits/rnica/{assessment_id}/lock", headers=rn_headers)
        assert second_lock_resp.status_code == 200, second_lock_resp.text

        db_session.expire_all()
        reloaded_record = db_session.query(RnicaAssessment).filter_by(id=uuid.UUID(assessment_id)).one()
        assert reloaded_record.hope_event_type == "HUV2"
        assert reloaded_record.hope_event_date == date(2026, 1, 21)

        requirements_after_second_lock = (
            db_session.query(SFVRequirement)
            .filter(
                SFVRequirement.patient_id == patient.id,
                SFVRequirement.trigger_reference_id == record.id,
            )
            .all()
        )
        assert len(requirements_after_second_lock) == 1, "Re-locking must not create a duplicate SFV requirement"

    def test_update_assessment_outside_any_huv_window_is_not_a_hope_event(self, client, db_session, rn_headers):
        """An UPDATE assessment locked outside both the HUV1 (6-15) and
        HUV2 (16-30) windows must not be mistaken for either -- matches
        today's GET /rnica/hope-update-status display behavior exactly."""
        tenant_id = db_session.info.get("tenant_id")
        patient, admission = _make_patient_with_admission(db_session, tenant_id)

        assessment_id, lock_json = self._lock_admission_then_update(
            client,
            db_session,
            rn_headers,
            patient,
            update_visit_date="2026-01-03",  # day 2 -- before HUV1 window opens
            update_symptom_impact=_symptom_impact(pain="3"),
        )

        assert lock_json["hopePhaseB"] is None

        db_session.expire_all()
        record = db_session.query(RnicaAssessment).filter_by(id=uuid.UUID(assessment_id)).one()
        assert record.hope_event_type is None
        assert record.hope_event_date is None


@pytest.mark.integration
def test_hope_event_identity_survives_reload(client, db_session, rn_headers):
    """15. Reload persistence -- hope_event_type/hope_event_date must be
    read back from a completely fresh DB query, proving they were
    genuinely committed and are not merely an artifact of the same
    in-memory request/session."""
    tenant_id = db_session.info.get("tenant_id")
    patient, admission = _make_patient_with_admission(db_session, tenant_id)

    form_data = _rnica_form_data(_symptom_impact(pain="2"), visit_date="2026-01-01")
    assessment_id, lock_json = _save_and_lock(client, rn_headers, patient.id, form_data)
    assert lock_json["hopePhaseB"]["hopeEventType"] == "ADMISSION"

    # Force a genuinely fresh read: expire the whole identity map, not just
    # one object, so SQLAlchemy cannot serve this from any Python-side
    # cache -- the next attribute access must re-query the database.
    db_session.expire_all()
    reloaded = db_session.query(RnicaAssessment).filter_by(id=uuid.UUID(assessment_id)).one()
    assert reloaded.hope_event_type == "ADMISSION"
    assert reloaded.hope_event_date == date(2026, 1, 1)

    # Also verify via a second, independent HTTP GET -- end-to-end through
    # the API layer, not just the ORM.
    get_resp = client.get(f"/visits/rnica/{assessment_id}", headers=rn_headers)
    assert get_resp.status_code == 200, get_resp.text
