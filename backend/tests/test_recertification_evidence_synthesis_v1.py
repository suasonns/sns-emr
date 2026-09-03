# tests/test_recertification_evidence_synthesis_v1.py
"""
Runtime patient-level synthesis tests (PR #59 production-grade extension).

Covers all 9 required representative scenarios plus the mandatory
read-only SQL write-audit integration test, against the same real,
freshly migrated isolated database used by
test_recertification_reasoning_framework_v1.py
(sns_emr_test_pr59_isolated) -- never the shared sns_emr_test database,
never a fabricated/mocked session.

Each test creates its own patient/tenant/user/benefit-period fixture data
(with fresh UUIDs derived from the test name, so tests never collide or
require destructive truncation of unrelated data) and commits it as real
setup, then calls build_recertification_evidence_summary() and asserts
only on its return value -- the function itself is never given write
access to anything.
"""
from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timezone
from urllib.parse import urlsplit, urlunsplit

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from app.core.database import DATABASE_URL as APP_DATABASE_URL
from app.main import fastapi_app as _fastapi_app  # noqa: F401  (forces full SQLAlchemy mapper registration)
from app.models.benefit_period import BenefitPeriod
from app.models.f2f_encounter import F2FEncounter
from app.models.patient import Patient
from app.models.patient_diagnosis import PatientDiagnosis
from app.models.rn_recert_assessment import RNRecertAssessment
from app.models.tenant import Tenant
from app.models.user import User

from app.services.recertification_evidence_synthesis import (
    RecertificationSynthesisError,
    build_recertification_evidence_summary,
)

_ISOLATED_TEST_DB_NAME = "sns_emr_test_pr59_isolated"


def _isolated_test_database_url() -> str:
    override = os.getenv("PR59_ISOLATED_TEST_DATABASE_URL")
    if override:
        return override
    parts = urlsplit(APP_DATABASE_URL)
    return urlunsplit(parts._replace(path=f"/{_ISOLATED_TEST_DB_NAME}"))


def _isolated_db_available() -> bool:
    url = _isolated_test_database_url()
    dbname = urlsplit(url).path.lstrip("/")
    if "test" not in dbname.lower():
        return False
    try:
        engine = create_engine(url, future=True, pool_pre_ping=True)
        with engine.connect() as conn:
            actual = conn.execute(text("SELECT current_database()")).scalar()
            has_patients_table = conn.execute(text(
                "SELECT to_regclass('public.patients') IS NOT NULL"
            )).scalar()
        engine.dispose()
        return actual == dbname and bool(has_patients_table)
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _isolated_db_available(),
    reason=(
        "Dedicated isolated database 'sns_emr_test_pr59_isolated' is not available/migrated. "
        "Build it once with: "
        "$env:TEST_DATABASE_URL=<url pointing at sns_emr_test_pr59_isolated>; python _create_test_db.py"
    ),
)


@pytest.fixture()
def db():
    isolated_url = _isolated_test_database_url()
    engine = create_engine(isolated_url, future=True, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _seed_id(test_name: str, kind: str) -> uuid.UUID:
    """Deterministic-per-test UUID so repeated runs reuse (rather than
    collide with) the same rows, and different tests never share rows."""
    return uuid.uuid5(uuid.NAMESPACE_URL, f"pr59-runtime-synthesis:{test_name}:{kind}")


def _seed_patient_scenario(
    db,
    test_name: str,
    *,
    primary_diagnosis_display: str = "Adult Failure to Thrive",
    primary_icd10: str = "R64",
):
    """Creates (or reuses) tenant/user/patient/two benefit periods for one
    test scenario. Returns (patient_id, hospice_episode_id, prior_bp_id,
    current_bp_id). hospice_episode_id is a caller-supplied opaque
    identifier per the review's own spec (this schema version has no
    dedicated HospiceEpisode table; it is not independently validated
    against an admissions table)."""
    tenant_id = _seed_id(test_name, "tenant")
    user_id = _seed_id(test_name, "user")
    patient_id = _seed_id(test_name, "patient")
    hospice_episode_id = _seed_id(test_name, "episode")
    prior_bp_id = _seed_id(test_name, "prior_bp")
    current_bp_id = _seed_id(test_name, "current_bp")

    if db.get(Tenant, tenant_id) is None:
        db.add(Tenant(
            id=tenant_id, legal_name=f"Test Hospice {test_name}", display_name=f"Test Hospice {test_name}",
            npi="1234567890",
        ))
    if db.get(User, user_id) is None:
        db.add(User(
            id=user_id, tenant_id=tenant_id, email=f"{test_name}@example.test",
            full_name="Test Physician", role="PHYSICIAN",
        ))
    db.flush()

    if db.get(Patient, patient_id) is None:
        db.add(Patient(
            id=patient_id, tenant_id=tenant_id, mrn=f"MRN-{test_name}",
            date_of_birth=date(1940, 1, 1), primary_diagnosis=primary_diagnosis_display,
            created_by=user_id,
        ))
    db.flush()

    if db.get(BenefitPeriod, prior_bp_id) is None:
        db.add(BenefitPeriod(
            id=prior_bp_id, tenant_id=tenant_id, patient_id=patient_id, benefit_type="INITIAL",
            period_number=1, election_date=date(2025, 1, 1), start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 1), is_current=False,
        ))
    if db.get(BenefitPeriod, current_bp_id) is None:
        db.add(BenefitPeriod(
            id=current_bp_id, tenant_id=tenant_id, patient_id=patient_id, benefit_type="RECERT",
            period_number=2, election_date=date(2025, 3, 1), start_date=date(2025, 3, 1),
            end_date=date(2025, 5, 1), is_current=True,
        ))
    existing_dx = (
        db.query(PatientDiagnosis)
        .filter(PatientDiagnosis.patient_id == patient_id, PatientDiagnosis.diagnosis_type == "PRIMARY")
        .one_or_none()
    )
    if existing_dx is None:
        db.add(PatientDiagnosis(
            id=_seed_id(test_name, "dx_primary"), tenant_id=tenant_id, patient_id=patient_id,
            diagnosis_type="PRIMARY", status="ACTIVE", source="ATTENDING_PHYSICIAN",
            icd10_code=primary_icd10, diagnosis_description=primary_diagnosis_display,
            display_name=primary_diagnosis_display, is_terminal=True, active=True,
            effective_date=date(2025, 1, 1), effective_benefit_period_number=1,
        ))
    db.commit()
    return patient_id, hospice_episode_id, user_id, prior_bp_id, current_bp_id


def _add_f2f(db, test_name, suffix, *, patient_id, tenant_id, benefit_period_id, performed_by_user_id, encounter_date, **fields):
    f2f_id = _seed_id(test_name, f"f2f_{suffix}")
    if db.get(F2FEncounter, f2f_id) is None:
        db.add(F2FEncounter(
            id=f2f_id, tenant_id=tenant_id, patient_id=patient_id, benefit_period_id=benefit_period_id,
            encounter_date=encounter_date, performed_by_role="MD", performed_by_user_id=performed_by_user_id,
            status="FINALIZED", finalized_at=datetime.combine(encounter_date, datetime.min.time(), tzinfo=timezone.utc),
            **fields,
        ))
        db.commit()
    return f2f_id


def _add_rn_recert(db, test_name, suffix, *, patient_id, tenant_id, benefit_period_id, created_by_user_id, finalized_at, **fields):
    rn_id = _seed_id(test_name, f"rn_{suffix}")
    if db.get(RNRecertAssessment, rn_id) is None:
        db.add(RNRecertAssessment(
            id=rn_id, tenant_id=tenant_id, patient_id=patient_id, benefit_period_id=benefit_period_id,
            created_by_user_id=created_by_user_id, status="FINALIZED", finalized_at=finalized_at, **fields,
        ))
        db.commit()
    return rn_id


def _tenant_id_for(test_name: str) -> uuid.UUID:
    return _seed_id(test_name, "tenant")


# ---------------------------------------------------------------------
# SCENARIO 1: Documented decline
# ---------------------------------------------------------------------

def test_scenario_1_documented_decline(db):
    test_name = "scenario_1_decline"
    patient_id, episode_id, user_id, prior_bp_id, current_bp_id = _seed_patient_scenario(db, test_name)
    tenant_id = _tenant_id_for(test_name)

    _add_f2f(
        db, test_name, "prior", patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=prior_bp_id,
        performed_by_user_id=user_id, encounter_date=date(2025, 2, 1),
        kps_score=60, pps_score_previous=60, pps_score_current=60, adl_dependency_level="PARTIAL",
        adl_dependency_count=2, oral_intake_decline=False, hospitalizations_30d=0,
    )
    _add_f2f(
        db, test_name, "current", patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=current_bp_id,
        performed_by_user_id=user_id, encounter_date=date(2025, 4, 1),
        kps_score=40, pps_score_previous=60, pps_score_current=40, adl_dependency_level="TOTAL",
        adl_dependency_count=4, oral_intake_decline=True, hospitalizations_30d=1,
    )

    result = build_recertification_evidence_summary(
        db, patient_id=patient_id, hospice_episode_id=episode_id,
        current_benefit_period_id=current_bp_id, prior_benefit_period_id=prior_bp_id,
        regulatory_context="CMS_MEDICARE_SIX_MONTH", generated_at=datetime.now(timezone.utc),
    )

    sections = {s["section_number"]: s for s in result["sections"]}
    assert sections[4]["content"]["PPS"]["comparison_label"] == "DECLINING"
    assert sections[4]["content"]["KPS"]["comparison_label"] == "DECLINING"
    assert sections[5]["content"]["adl_dependency_count_comparison"]["comparison_label"] == "DECLINING"
    assert sections[6]["content"]["oral_intake_decline"]["current"] is True
    assert sections[11]["content"]["hospitalizations_30d_comparison"]["comparison_label"] == "DECLINING"
    for forbidden in ("is eligible", "not eligible", "certify the patient", "prognosis met", "please recertify", "discharge recommended"):
        assert forbidden not in str(result).lower()


# ---------------------------------------------------------------------
# SCENARIO 2: Stability
# ---------------------------------------------------------------------

def test_scenario_2_stability(db):
    test_name = "scenario_2_stability"
    patient_id, episode_id, user_id, prior_bp_id, current_bp_id = _seed_patient_scenario(db, test_name)
    tenant_id = _tenant_id_for(test_name)

    _add_f2f(
        db, test_name, "prior", patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=prior_bp_id,
        performed_by_user_id=user_id, encounter_date=date(2025, 2, 1),
        kps_score=40, pps_score_previous=40, pps_score_current=40,
    )
    _add_f2f(
        db, test_name, "current", patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=current_bp_id,
        performed_by_user_id=user_id, encounter_date=date(2025, 4, 1),
        kps_score=40, pps_score_previous=40, pps_score_current=40,
    )

    result = build_recertification_evidence_summary(
        db, patient_id=patient_id, hospice_episode_id=episode_id,
        current_benefit_period_id=current_bp_id, prior_benefit_period_id=prior_bp_id,
        regulatory_context="CMS_MEDICARE_SIX_MONTH", generated_at=datetime.now(timezone.utc),
    )
    sections = {s["section_number"]: s for s in result["sections"]}
    assert sections[4]["content"]["PPS"]["comparison_label"] == "STABLE"
    assert sections[14]["content"]["overall_classification"] == "STABLE_WITH_CONTINUED_BURDEN"
    assert sections[19]["status"] == "POPULATED"
    assert any("stability" in q.lower() or "stable" in q.lower() for q in sections[19]["content"])
    for forbidden in ("ineligible", "discharge recommended"):
        assert forbidden not in str(result).lower()


# ---------------------------------------------------------------------
# SCENARIO 3: Improvement
# ---------------------------------------------------------------------

def test_scenario_3_improvement(db):
    test_name = "scenario_3_improvement"
    patient_id, episode_id, user_id, prior_bp_id, current_bp_id = _seed_patient_scenario(db, test_name)
    tenant_id = _tenant_id_for(test_name)

    _add_f2f(
        db, test_name, "prior", patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=prior_bp_id,
        performed_by_user_id=user_id, encounter_date=date(2025, 2, 1),
        pps_score_previous=30, pps_score_current=30,
    )
    _add_f2f(
        db, test_name, "current", patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=current_bp_id,
        performed_by_user_id=user_id, encounter_date=date(2025, 4, 1),
        pps_score_previous=30, pps_score_current=50,
    )

    result = build_recertification_evidence_summary(
        db, patient_id=patient_id, hospice_episode_id=episode_id,
        current_benefit_period_id=current_bp_id, prior_benefit_period_id=prior_bp_id,
        regulatory_context="CMS_MEDICARE_SIX_MONTH", generated_at=datetime.now(timezone.utc),
    )
    sections = {s["section_number"]: s for s in result["sections"]}
    assert sections[4]["content"]["PPS"]["comparison_label"] == "IMPROVING"
    assert sections[14]["content"]["overall_classification"] == "IMPROVED_WITH_CONTINUED_BURDEN"
    assert sections[20]["status"] == "POPULATED"
    assert any("improved" in e["text"] for e in sections[20]["content"])
    assert "discharge recommended" not in str(result).lower()


# ---------------------------------------------------------------------
# SCENARIO 4: Mixed clinical course
# ---------------------------------------------------------------------

def test_scenario_4_mixed_course(db):
    test_name = "scenario_4_mixed"
    patient_id, episode_id, user_id, prior_bp_id, current_bp_id = _seed_patient_scenario(db, test_name)
    tenant_id = _tenant_id_for(test_name)

    _add_f2f(
        db, test_name, "prior", patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=prior_bp_id,
        performed_by_user_id=user_id, encounter_date=date(2025, 2, 1),
        pps_score_previous=50, pps_score_current=50, weight_loss_lbs=0, hospitalizations_30d=1,
    )
    _add_f2f(
        db, test_name, "current", patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=current_bp_id,
        performed_by_user_id=user_id, encounter_date=date(2025, 4, 1),
        pps_score_previous=50, pps_score_current=50, weight_loss_lbs=8, hospitalizations_30d=0,
    )

    result = build_recertification_evidence_summary(
        db, patient_id=patient_id, hospice_episode_id=episode_id,
        current_benefit_period_id=current_bp_id, prior_benefit_period_id=prior_bp_id,
        regulatory_context="CMS_MEDICARE_SIX_MONTH", generated_at=datetime.now(timezone.utc),
    )
    sections = {s["section_number"]: s for s in result["sections"]}
    assert sections[4]["content"]["PPS"]["comparison_label"] == "STABLE"
    assert sections[6]["content"]["weight_loss_comparison"]["comparison_label"] == "DECLINING"
    assert sections[11]["content"]["hospitalizations_30d_comparison"]["comparison_label"] == "IMPROVING"
    # Each domain retains its own direction -- no forced single-direction conclusion.
    assert sections[14]["content"]["overall_classification"] == "MIXED_CLINICAL_COURSE"


# ---------------------------------------------------------------------
# SCENARIO 5: Missing prior baseline
# ---------------------------------------------------------------------

def test_scenario_5_missing_prior_baseline(db):
    test_name = "scenario_5_missing_prior"
    patient_id, episode_id, user_id, prior_bp_id, current_bp_id = _seed_patient_scenario(db, test_name)
    tenant_id = _tenant_id_for(test_name)

    _add_f2f(
        db, test_name, "current", patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=current_bp_id,
        performed_by_user_id=user_id, encounter_date=date(2025, 4, 1),
        pps_score_previous=None, pps_score_current=40,
    )

    result = build_recertification_evidence_summary(
        db, patient_id=patient_id, hospice_episode_id=episode_id,
        current_benefit_period_id=current_bp_id, prior_benefit_period_id=prior_bp_id,
        regulatory_context="CMS_MEDICARE_SIX_MONTH", generated_at=datetime.now(timezone.utc),
    )
    sections = {s["section_number"]: s for s in result["sections"]}
    assert sections[4]["content"]["PPS"]["comparison_label"] == "PRIOR_VALUE_MISSING"
    assert sections[17]["status"] == "POPULATED"
    assert any(m.get("label") == "PRIOR_VALUE_MISSING" for m in sections[17]["content"])
    # No inferred decline: the label is explicitly PRIOR_VALUE_MISSING, never DECLINING.
    assert sections[4]["content"]["PPS"]["comparison_label"] != "DECLINING"


# ---------------------------------------------------------------------
# SCENARIO 6: Conflicting documentation (same-date, cross-source)
# ---------------------------------------------------------------------

def test_scenario_6_conflicting_documentation(db):
    test_name = "scenario_6_conflict"
    patient_id, episode_id, user_id, prior_bp_id, current_bp_id = _seed_patient_scenario(db, test_name)
    tenant_id = _tenant_id_for(test_name)
    same_date = date(2025, 4, 1)

    _add_f2f(
        db, test_name, "current", patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=current_bp_id,
        performed_by_user_id=user_id, encounter_date=same_date,
        pps_score_previous=60, pps_score_current=40,
    )
    _add_rn_recert(
        db, test_name, "current", patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=current_bp_id,
        created_by_user_id=user_id, finalized_at=datetime.combine(same_date, datetime.min.time(), tzinfo=timezone.utc),
        pps_score=60,
    )

    result = build_recertification_evidence_summary(
        db, patient_id=patient_id, hospice_episode_id=episode_id,
        current_benefit_period_id=current_bp_id, prior_benefit_period_id=prior_bp_id,
        regulatory_context="CMS_MEDICARE_SIX_MONTH", generated_at=datetime.now(timezone.utc),
    )
    sections = {s["section_number"]: s for s in result["sections"]}
    assert sections[4]["content"]["PPS"]["comparison_label"] == "CONFLICTING_DOCUMENTATION"
    assert sections[16]["status"] == "POPULATED"
    conflict = sections[16]["content"][0]
    assert conflict["resolution_status"] == "UNRESOLVED"
    assert sorted(conflict["conflicting_values"]) == [40, 60]
    assert "physician_review_question" in conflict


# ---------------------------------------------------------------------
# SCENARIO 7: Reversible factor
# ---------------------------------------------------------------------

def test_scenario_7_reversible_factor(db):
    test_name = "scenario_7_reversible"
    patient_id, episode_id, user_id, prior_bp_id, current_bp_id = _seed_patient_scenario(db, test_name)
    tenant_id = _tenant_id_for(test_name)

    _add_f2f(
        db, test_name, "current", patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=current_bp_id,
        performed_by_user_id=user_id, encounter_date=date(2025, 4, 1),
        weight_loss_lbs=10, clinical_decline_summary="Weight loss attributed to aggressive diuresis for volume overload.",
    )

    result = build_recertification_evidence_summary(
        db, patient_id=patient_id, hospice_episode_id=episode_id,
        current_benefit_period_id=current_bp_id, prior_benefit_period_id=prior_bp_id,
        regulatory_context="CMS_MEDICARE_SIX_MONTH", generated_at=datetime.now(timezone.utc),
    )
    sections = {s["section_number"]: s for s in result["sections"]}
    assert sections[15]["status"] == "POPULATED"
    assert "diuresis" in sections[15]["content"]["matched_phrases"]
    assert any("reversible" in q.lower() for q in sections[19]["content"])


# ---------------------------------------------------------------------
# SCENARIO 8: Regulatory separation
# ---------------------------------------------------------------------

def test_scenario_8_regulatory_separation(db):
    test_name = "scenario_8_regulatory"
    patient_id, episode_id, user_id, prior_bp_id, current_bp_id = _seed_patient_scenario(db, test_name)

    result_cms = build_recertification_evidence_summary(
        db, patient_id=patient_id, hospice_episode_id=episode_id,
        current_benefit_period_id=current_bp_id, prior_benefit_period_id=prior_bp_id,
        regulatory_context="CMS_MEDICARE_SIX_MONTH", generated_at=datetime.now(timezone.utc),
    )
    result_ca = build_recertification_evidence_summary(
        db, patient_id=patient_id, hospice_episode_id=episode_id,
        current_benefit_period_id=current_bp_id, prior_benefit_period_id=prior_bp_id,
        regulatory_context="CALIFORNIA_CDPH_STATE", generated_at=datetime.now(timezone.utc),
    )
    cms_def = result_cms["sections"][0]["content"]["regulatory_context_definition"]
    ca_def = result_ca["sections"][0]["content"]["regulatory_context_definition"]
    assert cms_def["regulatory_authority"] != ca_def["regulatory_authority"]
    assert cms_def["source_reference"] != ca_def["source_reference"]
    assert cms_def != ca_def

    with pytest.raises(RecertificationSynthesisError):
        build_recertification_evidence_summary(
            db, patient_id=patient_id, hospice_episode_id=episode_id,
            current_benefit_period_id=current_bp_id, prior_benefit_period_id=prior_bp_id,
            regulatory_context="SOME_OTHER_CONTEXT", generated_at=datetime.now(timezone.utc),
        )


# ---------------------------------------------------------------------
# SCENARIO 9: Read-only SQL write audit
# ---------------------------------------------------------------------

def test_scenario_9_read_only_audit(db):
    test_name = "scenario_9_readonly"
    patient_id, episode_id, user_id, prior_bp_id, current_bp_id = _seed_patient_scenario(db, test_name)
    tenant_id = _tenant_id_for(test_name)
    _add_f2f(
        db, test_name, "current", patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=current_bp_id,
        performed_by_user_id=user_id, encounter_date=date(2025, 4, 1), pps_score_current=40,
    )

    captured_statements = []

    def _capture(conn, cursor, statement, parameters, context, executemany):
        captured_statements.append(statement)

    engine = db.get_bind()
    event.listen(engine, "before_cursor_execute", _capture)
    try:
        build_recertification_evidence_summary(
            db, patient_id=patient_id, hospice_episode_id=episode_id,
            current_benefit_period_id=current_bp_id, prior_benefit_period_id=prior_bp_id,
            regulatory_context="CMS_MEDICARE_SIX_MONTH", generated_at=datetime.now(timezone.utc),
        )
    finally:
        event.remove(engine, "before_cursor_execute", _capture)

    assert captured_statements, "Expected the synthesis call to issue at least one SELECT."
    for stmt in captured_statements:
        normalized = stmt.strip().split(None, 1)[0].upper()
        assert normalized == "SELECT", f"Read-only violation: non-SELECT statement issued during synthesis: {stmt!r}"


# ---------------------------------------------------------------------
# Additional structural guarantees
# ---------------------------------------------------------------------

def test_all_21_sections_always_present(db):
    test_name = "scenario_structural"
    patient_id, episode_id, user_id, prior_bp_id, current_bp_id = _seed_patient_scenario(db, test_name)
    result = build_recertification_evidence_summary(
        db, patient_id=patient_id, hospice_episode_id=episode_id,
        current_benefit_period_id=current_bp_id, prior_benefit_period_id=None,
        regulatory_context="CMS_MEDICARE_SIX_MONTH", generated_at=datetime.now(timezone.utc),
    )
    assert len(result["sections"]) == 21
    for section in result["sections"]:
        assert section["status"] in ("POPULATED", "EMPTY")
        if section["status"] == "EMPTY":
            assert section["reason"]


def test_source_traceability_fields_present_on_every_evidence_item(db):
    test_name = "scenario_traceability"
    patient_id, episode_id, user_id, prior_bp_id, current_bp_id = _seed_patient_scenario(db, test_name)
    tenant_id = _tenant_id_for(test_name)
    _add_f2f(
        db, test_name, "current", patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=current_bp_id,
        performed_by_user_id=user_id, encounter_date=date(2025, 4, 1), pps_score_current=40,
    )
    result = build_recertification_evidence_summary(
        db, patient_id=patient_id, hospice_episode_id=episode_id,
        current_benefit_period_id=current_bp_id, prior_benefit_period_id=prior_bp_id,
        regulatory_context="CMS_MEDICARE_SIX_MONTH", generated_at=datetime.now(timezone.utc),
    )
    trace_section = next(s for s in result["sections"] if s["section_number"] == 21)
    assert trace_section["content"], "Expected at least one evidence item in the audit trace."
    required_fields = {
        "evidence_id", "patient_id", "hospice_episode_id", "benefit_period_id", "period_role",
        "disease_id", "disease_name", "concept_domain", "concept_name", "exact_documented_value",
        "unit", "assessment_date", "documentation_date", "source_record_type", "source_record_id",
        "source_document_id", "author_or_assessor_id", "classification_rule_id", "framework_version",
        "generated_at", "read_only",
    }
    for item in trace_section["content"]:
        assert required_fields.issubset(item.keys())
        assert item["read_only"] is True


def test_no_forbidden_vocabulary_anywhere_in_output(db):
    test_name = "scenario_forbidden_vocab"
    patient_id, episode_id, user_id, prior_bp_id, current_bp_id = _seed_patient_scenario(db, test_name)
    result = build_recertification_evidence_summary(
        db, patient_id=patient_id, hospice_episode_id=episode_id,
        current_benefit_period_id=current_bp_id, prior_benefit_period_id=prior_bp_id,
        regulatory_context="CMS_MEDICARE_SIX_MONTH", generated_at=datetime.now(timezone.utc),
    )
    lowered = str(result).lower()
    for forbidden in (
        "not eligible", "not terminal", "do not certify", "prognosis met", "prognosis not met",
        "do not recertify", "discharge recommended",
    ):
        assert forbidden not in lowered
