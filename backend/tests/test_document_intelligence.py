from __future__ import annotations

import io
import json
import uuid
from datetime import date, datetime, timezone

import docx as docx_lib
from pypdf import PdfWriter

from app.models.document_record import DocumentRecord
from app.models.patient import Patient
from app.models.patient_evidence import PatientEvidenceRecord
from app.services.evidence import document_intelligence_service as dis
from app.services.evidence.document_harvest_job import run_document_intelligence
from tests.conftest import TEST_USER_ID


def _make_patient(db_session, tenant_id: uuid.UUID) -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"DOCINT-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1940, 1, 1),
        primary_diagnosis="Document intelligence test diagnosis",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _make_docx_bytes(paragraphs: list[str]) -> bytes:
    document = docx_lib.Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _make_blank_pdf_bytes() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


# ---------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------


def test_extract_text_from_plain_text_file():
    result = dis.extract_text_from_file(
        file_bytes=b"Sodium 128 mEq/L (LOW)\nPotassium 4.1 mEq/L",
        content_type="text/plain",
        file_name="labs.txt",
    )
    assert result.method == "plain_text"
    assert "Sodium 128" in result.text
    assert result.needs_manual_review is False


def test_extraction_result_strips_embedded_nul_bytes():
    """Scanned/OCR'd PDF text occasionally contains embedded NUL (0x00)
    bytes, which PostgreSQL text columns reject outright ("A string
    literal cannot contain NUL (0x00) characters"), previously failing
    the entire document with no text, no AI findings, and no evidence.
    Every ExtractionResult must come out NUL-free regardless of source."""
    result = dis.ExtractionResult(text="Sodium 128\x00 mEq/L", method="ocr")
    assert "\x00" not in result.text
    assert result.text == "Sodium 128 mEq/L"


def test_extract_text_from_plain_text_file_strips_nul_bytes():
    result = dis.extract_text_from_file(
        file_bytes=b"Sodium 128\x00 mEq/L (LOW)",
        content_type="text/plain",
        file_name="labs.txt",
    )
    assert "\x00" not in result.text
    assert result.text == "Sodium 128 mEq/L (LOW)"


def test_extract_text_from_docx_includes_paragraphs_and_tables():
    file_bytes = _make_docx_bytes(
        ["History and Physical", "Patient reports significant functional decline over 3 months."]
    )
    result = dis.extract_text_from_file(
        file_bytes=file_bytes,
        content_type=dis.DOCX_CONTENT_TYPE,
        file_name="hnp.docx",
    )
    assert result.method == "docx"
    assert "functional decline" in result.text
    assert result.needs_manual_review is False


def test_extract_text_from_scanned_pdf_flags_manual_review():
    # A blank PDF page has no extractable text layer -- simulates a
    # scanned/image-only PDF, which v1 does not silently guess at.
    file_bytes = _make_blank_pdf_bytes()
    result = dis.extract_text_from_file(
        file_bytes=file_bytes,
        content_type="application/pdf",
        file_name="scanned.pdf",
    )
    assert result.text == ""
    assert result.needs_manual_review is True


def test_extract_text_from_image_defers_to_vision_path():
    result = dis.extract_text_from_file(
        file_bytes=b"\xff\xd8\xff\xe0fake-jpeg-bytes",
        content_type="image/jpeg",
        file_name="photo.jpg",
    )
    assert result.method == "vision"
    assert result.image_base64 is not None
    assert result.needs_manual_review is False


def test_extract_text_from_unsupported_type_flags_manual_review():
    result = dis.extract_text_from_file(
        file_bytes=b"legacy word doc bytes",
        content_type="application/msword",
        file_name="old.doc",
    )
    assert result.method == "unsupported"
    assert result.needs_manual_review is True


# ---------------------------------------------------------------------
# AI classification inertness / parsing
# ---------------------------------------------------------------------


def test_classify_and_extract_document_is_inert_when_unconfigured(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT", raising=False)

    assert dis.is_configured() is False

    result = dis.classify_and_extract_document(
        text="Sodium 128 mEq/L (LOW)",
        content_type="text/plain",
    )
    assert result is None


def test_classify_and_extract_document_parses_well_formed_response(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://fake-resource.openai.azure.com/openai/v1")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "fake-key")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5.4")

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "document_type_guess": "LABS_DIAGNOSTICS",
                                    "summary": "Basic metabolic panel showing low sodium.",
                                    "confidence": 0.9,
                                    "key_findings": [
                                        {
                                            "label": "Sodium",
                                            "value": "128 mEq/L (LOW)",
                                            "category": "lab_result",
                                            "original_text_excerpt": "Sodium 128 mEq/L (LOW)",
                                        },
                                        {
                                            # Malformed -- missing value, should be skipped.
                                            "label": "Potassium",
                                        },
                                    ],
                                }
                            )
                        }
                    }
                ]
            }

    def _fake_post(url, headers=None, json=None, timeout=None):
        assert "fake-resource.openai.azure.com" in url
        assert "gpt-5.4" in url
        return _FakeResponse()

    monkeypatch.setattr(dis.httpx, "post", _fake_post)

    result = dis.classify_and_extract_document(
        text="Sodium 128 mEq/L (LOW)\nPotassium 4.1 mEq/L",
        content_type="text/plain",
    )

    assert result is not None
    assert result.document_type_guess == "LABS_DIAGNOSTICS"
    assert result.confidence == 0.9
    assert len(result.key_findings) == 1
    assert result.key_findings[0].label == "Sodium"
    assert "128" in result.key_findings[0].value


# ---------------------------------------------------------------------
# End-to-end job wiring
# ---------------------------------------------------------------------


def test_run_document_intelligence_populates_text_and_harvests(
    db_session, monkeypatch, tmp_path
):
    """Uploads a real file to a temp local storage root, runs the job, and
    verifies document_text/extracted_values get populated and an evidence
    record is harvested -- with AI unconfigured (so no network calls),
    proving the pipeline degrades gracefully end to end."""

    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT", raising=False)

    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)

    from app.services import document_storage as storage_module

    storage_module.get_document_storage.cache_clear()
    monkeypatch.setenv("DOCUMENT_STORAGE_PROVIDER", "local")
    monkeypatch.setenv("DOCUMENT_STORAGE_DIR", str(tmp_path))

    document_id = uuid.uuid4()
    object_key = storage_module.build_document_key(
        tenant_id=tenant_id,
        patient_id=patient.id,
        document_id=document_id,
        content_type="text/plain",
    )
    storage = storage_module.get_document_storage()
    storage.put(
        object_key,
        io.BytesIO(b"Sodium 128 mEq/L (LOW). Patient reports worsening fatigue."),
        content_type="text/plain",
        max_bytes=storage_module.max_upload_bytes_from_env(),
    )

    doc = DocumentRecord(
        id=document_id,
        tenant_id=tenant_id,
        patient_id=patient.id,
        document_type="LABS",
        source="EXTERNAL",
        file_name="labs.txt",
        file_path=object_key,
        extracted_values={},
        document_text=None,
        uploaded_by=TEST_USER_ID,
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add(doc)
    db_session.commit()

    # Patch SessionLocal used inside the job to return connections bound to
    # the same test engine/transaction as db_session's fixture.
    from app.services.evidence import document_harvest_job as job_module

    monkeypatch.setattr(job_module, "SessionLocal", lambda: db_session.get_bind().pool and _TestSessionProxy(db_session))

    run_document_intelligence(document_id=document_id)

    db_session.expire_all()
    refreshed = db_session.get(DocumentRecord, document_id)
    assert refreshed.document_text is not None
    assert "Sodium 128" in refreshed.document_text
    assert refreshed.extracted_values.get("ai_needs_manual_review") is False

    evidence_records = (
        db_session.query(PatientEvidenceRecord)
        .filter(PatientEvidenceRecord.source_record_id == document_id)
        .all()
    )
    assert len(evidence_records) == 1
    assert "Sodium 128" in evidence_records[0].original_documentation


def test_run_document_intelligence_auto_populates_facesheet_from_hnp_text(
    db_session, monkeypatch, tmp_path
):
    """An uploaded document whose text parses as an HNP record (name/MRN/DOB
    present) must auto-populate the patient's facesheet and primary
    diagnosis via the SAME shared persist_patient_from_hnp_extraction()
    service /patients/from-hnp uses -- with source_document_id stamped for
    provenance. AI is left unconfigured so no network calls occur."""

    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT", raising=False)

    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)

    from app.services import document_storage as storage_module

    storage_module.get_document_storage.cache_clear()
    monkeypatch.setenv("DOCUMENT_STORAGE_PROVIDER", "local")
    monkeypatch.setenv("DOCUMENT_STORAGE_DIR", str(tmp_path))

    hnp_text = (
        "Name: Test Patient\n"
        "MRN: DOCINT-HNP-001\n"
        "Date of birth: 03/14/1945\n"
        "Sex: Female\n"
        "Address: 100 Sample Ave\n"
        "Diagnosis: Chronic obstructive pulmonary disease Noted on: 2026-01-05\n"
    )

    document_id = uuid.uuid4()
    object_key = storage_module.build_document_key(
        tenant_id=tenant_id,
        patient_id=patient.id,
        document_id=document_id,
        content_type="text/plain",
    )
    storage = storage_module.get_document_storage()
    storage.put(
        object_key,
        io.BytesIO(hnp_text.encode("utf-8")),
        content_type="text/plain",
        max_bytes=storage_module.max_upload_bytes_from_env(),
    )

    doc = DocumentRecord(
        id=document_id,
        tenant_id=tenant_id,
        patient_id=patient.id,
        document_type="HNP",
        source="EXTERNAL",
        file_name="hnp.txt",
        file_path=object_key,
        extracted_values={},
        document_text=None,
        uploaded_by=TEST_USER_ID,
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add(doc)
    db_session.commit()

    from app.services.evidence import document_harvest_job as job_module

    monkeypatch.setattr(
        job_module,
        "SessionLocal",
        lambda: db_session.get_bind().pool and _TestSessionProxy(db_session),
    )

    run_document_intelligence(document_id=document_id)

    db_session.expire_all()

    from app.models.patient_facesheet import PatientFaceSheet

    facesheet = (
        db_session.query(PatientFaceSheet)
        .filter(PatientFaceSheet.patient_id == patient.id)
        .one()
    )
    assert facesheet.first_name == "Test"
    assert facesheet.last_name == "Patient"
    assert "obstructive" in (facesheet.secondary_diagnoses or "").lower() or (
        facesheet.primary_diagnosis
    )
    assert facesheet.source_document_id == document_id

    # Existing patient's MRN is authoritative and is never overwritten by
    # a document-extracted value (persist_patient_from_hnp_extraction only
    # backfills mrn when the existing patient record has none).
    refreshed_patient = db_session.get(Patient, patient.id)
    assert refreshed_patient.mrn == patient.mrn


def test_run_document_intelligence_never_overwrites_existing_patient_name(
    db_session, monkeypatch, tmp_path
):
    """Real production defect, found via manual multi-document upload
    validation: this facesheet-auto-populate step runs unconditionally on
    EVERY uploaded document's extracted text, not just genuine H&P
    records. A lower-confidence document (an insurance authorization form,
    a cover letter, an orders packet) can incidentally satisfy
    parse_hnp_text's generic "Name:"/"MRN:"/"Date of birth:" patterns on
    unrelated text and silently overwrite a patient's real, previously-
    confirmed name with garbage. Once a facesheet already has a name, a
    later document's parse must never overwrite it -- only backfill a
    genuinely missing name, exactly like the existing mrn policy."""

    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT", raising=False)

    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)

    from app.models.patient_facesheet import PatientFaceSheet

    facesheet = PatientFaceSheet(
        tenant_id=tenant_id,
        patient_id=patient.id,
        first_name="Margaret",
        last_name="Kessler",
        dob=patient.date_of_birth,
        primary_diagnosis=patient.primary_diagnosis,
        created_by=TEST_USER_ID,
        updated_by=TEST_USER_ID,
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(facesheet)
    db_session.commit()

    from app.services import document_storage as storage_module

    storage_module.get_document_storage.cache_clear()
    monkeypatch.setenv("DOCUMENT_STORAGE_PROVIDER", "local")
    monkeypatch.setenv("DOCUMENT_STORAGE_DIR", str(tmp_path))

    # An unrelated document (e.g. an insurance authorization) whose OCR
    # text incidentally contains enough matching fields to pass
    # parse_hnp_text's minimal validation, with a name that does NOT
    # belong to this patient -- reproducing the real defect exactly.
    unrelated_text = (
        "Name: Birth Order\n"
        f"MRN: {patient.mrn}\n"
        f"Date of birth: {patient.date_of_birth.strftime('%m/%d/%Y')}\n"
        "Diagnosis: Authorization pending Noted on: 2026-01-05\n"
    )

    document_id = uuid.uuid4()
    object_key = storage_module.build_document_key(
        tenant_id=tenant_id,
        patient_id=patient.id,
        document_id=document_id,
        content_type="text/plain",
    )
    storage = storage_module.get_document_storage()
    storage.put(
        object_key,
        io.BytesIO(unrelated_text.encode("utf-8")),
        content_type="text/plain",
        max_bytes=storage_module.max_upload_bytes_from_env(),
    )

    doc = DocumentRecord(
        id=document_id,
        tenant_id=tenant_id,
        patient_id=patient.id,
        document_type="INSURANCE_AUTHORIZATION",
        source="EXTERNAL",
        file_name="auth.txt",
        file_path=object_key,
        extracted_values={},
        document_text=None,
        uploaded_by=TEST_USER_ID,
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add(doc)
    db_session.commit()

    from app.services.evidence import document_harvest_job as job_module

    monkeypatch.setattr(
        job_module,
        "SessionLocal",
        lambda: db_session.get_bind().pool and _TestSessionProxy(db_session),
    )

    run_document_intelligence(document_id=document_id)

    db_session.expire_all()

    refreshed_facesheet = (
        db_session.query(PatientFaceSheet)
        .filter(PatientFaceSheet.patient_id == patient.id)
        .one()
    )
    assert refreshed_facesheet.first_name == "Margaret"
    assert refreshed_facesheet.last_name == "Kessler"


class _TestSessionProxy:
    """Thin proxy so the job's `db.close()` calls don't tear down the
    shared test session/transaction that the pytest fixture owns."""

    def __init__(self, real_session):
        self._real = real_session

    def __getattr__(self, name):
        if name == "close":
            return lambda: None
        return getattr(self._real, name)
