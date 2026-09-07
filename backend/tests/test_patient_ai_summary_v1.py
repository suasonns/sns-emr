from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from app.billing.models.facility_collection_alert import FacilityCollectionAlert
from app.models.benefit_period import BenefitPeriod
from app.models.enums import TaskDiscipline, TaskOrigin, TaskStatus, TaskType
from app.models.patient_facesheet import PatientFaceSheet
from app.models.task import Task
from app.services import patient_ai_summary_service
from tests.conftest import TEST_USER_ID
from tests.test_aging_report_service import _enable_billing_for_tenant, _headers, _make_patient


def _make_facesheet(db_session, tenant_id: uuid.UUID, patient_id: uuid.UUID, *, first_name: str, last_name: str) -> None:
    db_session.add(
        PatientFaceSheet(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            patient_id=patient_id,
            first_name=first_name,
            last_name=last_name,
            created_by=TEST_USER_ID,
        )
    )
    db_session.commit()


def _make_benefit_period(db_session, tenant_id: uuid.UUID, patient_id: uuid.UUID) -> BenefitPeriod:
    period = BenefitPeriod(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        benefit_type="INITIAL",
        period_number=1,
        election_date=date(2026, 1, 1),
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        is_current=True,
        created_by=TEST_USER_ID,
    )
    db_session.add(period)
    db_session.commit()
    return period


def _make_task(db_session, tenant_id: uuid.UUID, patient_id: uuid.UUID) -> Task:
    task = Task(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        created_by=TEST_USER_ID,
        task_type=TaskType.HUV1,
        origin=TaskOrigin.SYSTEM_GENERATED if hasattr(TaskOrigin, "SYSTEM_GENERATED") else list(TaskOrigin)[0],
        discipline=list(TaskDiscipline)[0],
        status=TaskStatus.PENDING,
        due_date=date(2026, 2, 1),
    )
    db_session.add(task)
    db_session.commit()
    return task


def _make_alert(db_session, tenant_id: uuid.UUID, patient_id: uuid.UUID) -> FacilityCollectionAlert:
    alert = FacilityCollectionAlert(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        alert_type="OVERDUE_90",
        severity="HIGH",
        status="OPEN",
        outstanding_amount=1250.50,
        days_outstanding=91,
    )
    db_session.add(alert)
    db_session.commit()
    return alert


# ---------------------------------------------------------------------
# Service-level unit tests (no DB, no network) -- deterministic fallback
# always available, and never raises.
# ---------------------------------------------------------------------


def test_fallback_summary_used_when_not_configured(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT", raising=False)

    context = {
        "full_name": "Jane Doe",
        "primary_diagnosis": "Adult failure to thrive",
        "secondary_diagnoses": ["Dementia"],
        "benefit_period": {"benefit_type": "INITIAL", "period_number": 1},
        "recent_visits": [{"visit_type": "ROUTINE", "visit_datetime": "2026-01-01T00:00:00+00:00"}],
        "recent_notes": [{"note_type": "RN_RECERT"}],
        "open_tasks": [{"task_type": "HUV1", "due_date": "2026-02-01"}],
        "open_alerts": [{"alert_type": "OVERDUE_90", "severity": "HIGH", "outstanding_amount": 1250.5}],
    }

    summary = patient_ai_summary_service.generate_patient_ai_summary(context)

    assert summary.ai_generated is False
    assert summary.model is None
    assert "Jane Doe" in summary.hospice_clinical_picture
    assert any("Dementia" in item for item in summary.primary_hospice_drivers)
    assert any("Adult failure to thrive" in item for item in summary.evidence_of_decline)
    assert any("visit" in item.lower() for item in summary.recent_clinical_events)
    assert any("HUV1" in item for item in summary.open_operational_concerns)
    assert any("OVERDUE_90" in item for item in summary.open_operational_concerns)


def test_hospice_diagnosis_prioritization_leads_with_driver_not_first_diagnosis():
    """CHF (a hospice driver) must lead the narrative even when a
    non-driver diagnosis (CKD/anemia) is labeled "primary" in the raw
    chart data -- this is the exact Loren regression the prioritization
    logic exists to prevent."""
    context = {
        "full_name": "Loren B Shields",
        "primary_diagnosis": "Anemia due to CKD stage 3A",
        "secondary_diagnoses": [
            "Chronic systolic heart failure",
            "Moderate protein calorie malnutrition",
            "Right dominant hemiplegia/hemiparesis, late effect of stroke",
            "Type 2 diabetes with peripheral neuropathy",
            "Hyperlipidemia",
        ],
        "benefit_period": None,
        "recent_visits": [],
        "recent_notes": [],
        "open_tasks": [],
        "open_alerts": [],
    }

    summary = patient_ai_summary_service.generate_patient_ai_summary(context)

    assert any("heart failure" in item.lower() for item in summary.primary_hospice_drivers)
    assert any("malnutrition" in item.lower() for item in summary.evidence_of_decline)
    assert any("hemiplegia" in item.lower() for item in summary.evidence_of_decline)
    assert any("ckd" in item.lower() or "anemia" in item.lower() for item in summary.major_comorbidities)

    picture = summary.hospice_clinical_picture.lower()
    driver_index = picture.find("heart failure")
    ckd_index = picture.find("ckd")
    assert driver_index != -1
    # CHF (hospice driver) must appear before CKD in the narrative, not after.
    assert ckd_index == -1 or driver_index < ckd_index


def test_fallback_summary_never_raises_on_empty_context(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)

    summary = patient_ai_summary_service.generate_patient_ai_summary({})

    assert summary.ai_generated is False
    assert summary.hospice_clinical_picture
    assert summary.primary_hospice_drivers == ()
    assert summary.evidence_of_decline == ()
    assert summary.major_comorbidities == ()
    assert summary.recent_clinical_events == ()
    assert summary.clinical_risks
    assert summary.open_operational_concerns


def test_ai_path_used_when_configured_and_call_succeeds(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "test-deployment")

    def fake_call(context, config):
        return patient_ai_summary_service.PatientAiSummary(
            hospice_clinical_picture="AI-generated hospice clinical picture.",
            primary_hospice_drivers=("AI driver",),
            evidence_of_decline=("AI decline evidence",),
            major_comorbidities=("AI comorbidity",),
            recent_clinical_events=("AI event",),
            clinical_risks=(),
            open_operational_concerns=("AI concern",),
            generated_at=datetime.now(timezone.utc).isoformat(),
            model=config["deployment"],
            ai_generated=True,
        )

    monkeypatch.setattr(patient_ai_summary_service, "_call_azure_openai", fake_call)

    summary = patient_ai_summary_service.generate_patient_ai_summary({"full_name": "Jane Doe"})

    assert summary.ai_generated is True
    assert summary.model == "test-deployment"
    assert summary.hospice_clinical_picture == "AI-generated hospice clinical picture."


def test_ai_path_falls_back_when_call_fails(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "test-deployment")

    def fake_call_raises(context, config):
        raise RuntimeError("simulated network failure")

    monkeypatch.setattr(patient_ai_summary_service, "_call_azure_openai", fake_call_raises)

    summary = patient_ai_summary_service.generate_patient_ai_summary({"full_name": "Jane Doe"})

    assert summary.ai_generated is False
    assert "Jane Doe" in summary.hospice_clinical_picture


# ---------------------------------------------------------------------
# Endpoint-level tests -- always force the deterministic fallback path
# (no real network calls in tests) by monkeypatching the Azure config
# lookup to report "not configured".
# ---------------------------------------------------------------------


def test_patient_ai_summary_endpoint_returns_gathered_facts(client, db_session, monkeypatch):
    monkeypatch.setattr(patient_ai_summary_service, "_azure_openai_config", lambda: None)

    tenant_id = uuid.uuid4()
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="AI Summary Test Agency")
    patient = _make_patient(db_session, tenant_id, mrn_prefix="AIS1")
    _make_facesheet(db_session, tenant_id, patient.id, first_name="Jane", last_name="Doe")
    _make_benefit_period(db_session, tenant_id, patient.id)
    _make_task(db_session, tenant_id, patient.id)
    _make_alert(db_session, tenant_id, patient.id)

    headers = _headers("ADMINISTRATOR", tenant_id)
    response = client.get(f"/patient-charts/{patient.id}/ai-summary", headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["patient"]["id"] == str(patient.id)
    assert body["ai_generated"] is False
    assert body["model"] is None
    assert "Jane Doe" in body["hospice_clinical_picture"]
    assert "recent_clinical_events" in body
    assert any("HUV1" in item for item in body["open_operational_concerns"])
    assert any("OVERDUE_90" in item for item in body["open_operational_concerns"])
    assert body["generated_at"]


def test_patient_ai_summary_endpoint_cross_tenant_not_found(client, db_session, monkeypatch):
    monkeypatch.setattr(patient_ai_summary_service, "_azure_openai_config", lambda: None)

    tenant_id = uuid.uuid4()
    _enable_billing_for_tenant(db_session, tenant_id, legal_name="AI Summary Test Agency 2")
    patient = _make_patient(db_session, tenant_id, mrn_prefix="AIS2")

    other_tenant_headers = _headers("ADMINISTRATOR", uuid.uuid4())
    response = client.get(f"/patient-charts/{patient.id}/ai-summary", headers=other_tenant_headers)

    assert response.status_code == 404
