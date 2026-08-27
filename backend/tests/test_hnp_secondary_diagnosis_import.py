from __future__ import annotations

import uuid

import pytest

from app.api import patients as patients_api
from app.models.diagnosis_source import DiagnosisSource as DiagnosisSourceRecord
from app.models.enums import DiagnosisStatus
from app.models.patient_diagnosis import PatientDiagnosis
from app.services.hnp_parser_service import build_hnp_summary


def _hnp_text(*diagnoses: tuple[str, str], mrn: str = "HNP-12345") -> str:
    lines = [
        "Name: Loren Shields",
        f"MRN: {mrn}",
        "Date of birth: 07/25/1950",
        "Sex: Male",
        "Address: 11906 Kingston St",
    ]
    for description, noted_on in diagnoses:
        lines.append(f"Diagnosis: {description} Noted on: {noted_on}")
    return "\n".join(lines)


def _enriched_entries(raw_text: str) -> list[dict]:
    summary = build_hnp_summary(raw_text)
    entries = list(summary["diagnosis_entries"])
    for entry in entries:
        icd10_code, diagnosis_description, display_name = (
            patients_api._resolve_hnp_diagnosis_for_secondary_use(
                db=None,
                diagnosis_text=entry["description"],
            )
        )
        entry["icd10_code"] = icd10_code
        entry["diagnosis_description"] = diagnosis_description
        entry["display_name"] = display_name
    return entries


class _QueryStub:
    def __init__(self, rows, *, first_result=True):
        self._rows = list(rows)
        self._first_result = first_result

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return list(self._rows)

    def first(self):
        if not self._first_result:
            return None
        return self._rows[0] if self._rows else None


class _InspectorStub:
    @staticmethod
    def has_table(name: str) -> bool:
        return name == "diagnosis_sources"


class FakeDB:
    def __init__(self, patient_diagnoses=None, diagnosis_sources=None):
        self.patient_diagnoses = list(patient_diagnoses or [])
        self.diagnosis_sources = list(diagnosis_sources or [])
        self.added: list[object] = []

    def query(self, model):
        if model is PatientDiagnosis:
            return _QueryStub(self.patient_diagnoses)
        if model is DiagnosisSourceRecord:
            return _QueryStub(self.diagnosis_sources, first_result=False)
        return _QueryStub([])

    def add(self, obj):
        self.added.append(obj)
        if isinstance(obj, PatientDiagnosis):
            self.patient_diagnoses.append(obj)
        if isinstance(obj, DiagnosisSourceRecord):
            self.diagnosis_sources.append(obj)

    def get_bind(self):
        return object()


@pytest.fixture(autouse=True)
def _patch_inspect(monkeypatch):
    monkeypatch.setattr(patients_api, "inspect", lambda bind: _InspectorStub())


def _persisted_secondary_rows(fake_db: FakeDB, raw_text: str) -> tuple[list[PatientDiagnosis], list[dict]]:
    entries = _enriched_entries(raw_text)
    patients_api._sync_hnp_secondary_diagnoses(
        fake_db,
        tenant_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        source_name="Referral H&P",
        diagnosis_entries=entries,
    )
    rows = [item for item in fake_db.added if isinstance(item, PatientDiagnosis)]
    return rows, entries


def test_multiple_cardiac_secondaries_all_surface_as_candidates():
    rows, entries = _persisted_secondary_rows(
        FakeDB(),
        _hnp_text(
            ("Chronic systolic (congestive) heart failure (I50.22)", "05/22/2024"),
            ("Atherosclerotic heart disease of native coronary artery without angina pectoris (I25.10)", "05/22/2024"),
            ("Other forms of angina pectoris (I20.89)", "05/22/2024"),
            ("Venous insufficiency (chronic) (peripheral) (I87.2)", "05/22/2024"),
            ("Urinary tract infection, site not specified (N39.0)", "05/22/2024"),
            ("Moderate protein-calorie malnutrition (E44.0)", "05/22/2024"),
        ),
    )

    codes = {row.icd10_code for row in rows}
    assert {"I25.10", "I20.89", "I87.2", "N39.0", "E44.0"}.issubset(codes)
    summary_text = patients_api._build_hnp_secondary_summary(entries)
    assert "Atherosclerotic heart disease" in summary_text
    assert "Moderate protein-calorie malnutrition" in summary_text


def test_pneumonia_only_evidence_still_surfaces():
    rows, entries = _persisted_secondary_rows(
        FakeDB(),
        _hnp_text(
            ("Chronic systolic (congestive) heart failure (I50.22)", "05/22/2024"),
            ("Human metapneumovirus pneumonia (J12.3)", "05/22/2024"),
        ),
    )

    assert [row.icd10_code for row in rows] == ["J12.3"]
    assert "Human metapneumovirus pneumonia" in patients_api._build_hnp_secondary_summary(entries)


def test_duplicate_icd10_entries_are_deduplicated():
    rows, _ = _persisted_secondary_rows(
        FakeDB(),
        _hnp_text(
            ("Chronic systolic (congestive) heart failure (I50.22)", "05/22/2024"),
            ("Human metapneumovirus pneumonia (J12.3)", "05/22/2024"),
            ("Human metapneumovirus pneumonia (J12.3)", "05/23/2024"),
        ),
    )

    assert len(rows) == 1
    assert rows[0].icd10_code == "J12.3"


def test_negated_diagnoses_are_suppressed():
    rows, _ = _persisted_secondary_rows(
        FakeDB(),
        _hnp_text(
            ("Chronic systolic (congestive) heart failure (I50.22)", "05/22/2024"),
            ("Ruled out myocardial infarction (I21.9)", "05/22/2024"),
            ("Urinary tract infection, site not specified (N39.0)", "05/22/2024"),
        ),
    )

    codes = {row.icd10_code for row in rows}
    assert "I21.9" not in codes
    assert "N39.0" in codes


def test_historical_only_diagnoses_are_marked_historical_not_active():
    rows, entries = _persisted_secondary_rows(
        FakeDB(),
        _hnp_text(
            ("Chronic systolic (congestive) heart failure (I50.22)", "05/22/2024"),
            ("History of stroke (I63.9)", "01/01/2022"),
        ),
    )

    assert entries[1]["status"] == "historical"
    assert len(rows) == 1
    assert rows[0].status == DiagnosisStatus.HISTORICAL
    assert rows[0].active is False


def test_symptom_only_evidence_is_not_promoted_to_diagnosis():
    rows, entries = _persisted_secondary_rows(
        FakeDB(),
        _hnp_text(
            ("Chronic systolic (congestive) heart failure (I50.22)", "05/22/2024"),
            ("Shortness of breath (R06.02)", "05/22/2024"),
        ),
    )

    assert entries[1]["status"] == "symptom_only"
    assert rows == []


def test_unrelated_documented_comorbidities_still_surface():
    rows, _ = _persisted_secondary_rows(
        FakeDB(),
        _hnp_text(
            ("Chronic systolic (congestive) heart failure (I50.22)", "05/22/2024"),
            ("Urinary tract infection, site not specified (N39.0)", "05/22/2024"),
            ("Moderate protein-calorie malnutrition (E44.0)", "05/22/2024"),
        ),
    )

    codes = {row.icd10_code for row in rows}
    assert codes == {"N39.0", "E44.0"}


def test_secondary_persistence_keeps_provenance_in_diagnosis_and_source_rows():
    fake_db = FakeDB()
    tenant_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    entries = _enriched_entries(
        _hnp_text(
            ("Chronic systolic (congestive) heart failure (I50.22)", "05/22/2024"),
            ("Human metapneumovirus pneumonia (J12.3)", "05/22/2024"),
        )
    )

    patients_api._sync_hnp_diagnosis_sources(
        fake_db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        source_name="Referral H&P",
        diagnosis_entries=entries,
    )
    patients_api._sync_hnp_secondary_diagnoses(
        fake_db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        actor_id=actor_id,
        source_name="Referral H&P",
        diagnosis_entries=entries,
    )

    diagnosis_rows = [item for item in fake_db.added if isinstance(item, PatientDiagnosis)]
    source_rows = [item for item in fake_db.added if isinstance(item, DiagnosisSourceRecord)]

    assert len(diagnosis_rows) == 1
    assert diagnosis_rows[0].icd10_code == "J12.3"
    assert diagnosis_rows[0].supporting_evidence_summary == (
        "Imported from Referral H&P documented diagnosis noted on 2024-05-22."
    )

    assert any(
        row.dx_type == "SECONDARY"
        and row.icd_code == "J12.3"
        and row.description == "Human metapneumovirus pneumonia (J12.3)"
        and row.is_active is True
        for row in source_rows
    )
