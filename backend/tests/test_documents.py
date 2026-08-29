from __future__ import annotations

import shutil
import uuid
from datetime import date
from pathlib import Path

import pytest

from app.core.security import create_access_token
from app.models.document_record import DocumentRecord
from app.models.patient import Patient
from app.models.tenant import Tenant
from app.models.user import User
from app.services.document_storage import get_document_storage
from tests.conftest import TEST_USER_ID


def _headers(user_id: uuid.UUID, role: str, tenant_id: uuid.UUID) -> dict[str, str]:
    token = create_access_token(
        user_id=user_id,
        role=role,
        tenant_id=tenant_id,
        email=f"{role.lower()}@example.com",
    )
    return {"Authorization": f"Bearer {token}"}


def _make_patient(db_session, tenant_id: uuid.UUID, *, mrn_prefix: str = "DOC") -> Patient:
    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=f"{mrn_prefix}-{uuid.uuid4().hex[:10]}",
        date_of_birth=date(1947, 7, 7),
        primary_diagnosis="Hospice document verification diagnosis",
        status="ACTIVE",
        admission_status="ADMITTED",
        created_by=TEST_USER_ID,
    )
    db_session.add(patient)
    db_session.commit()
    return patient


def _ensure_tenant_and_user(db_session, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
    if db_session.get(Tenant, tenant_id) is None:
        db_session.add(
            Tenant(
                id=tenant_id,
                legal_name=f"Tenant {tenant_id.hex[:8]}",
                display_name=f"Tenant {tenant_id.hex[:8]}",
                npi=f"{int(str(tenant_id.int)[:10]):010d}",
                tenant_type="DEV",
                status="ACTIVE",
            )
        )
        db_session.commit()
    if db_session.get(User, user_id) is None:
        db_session.add(
            User(
                id=user_id,
                tenant_id=tenant_id,
                email=f"user.{user_id.hex[:8]}@example.com",
                full_name="Document Test User",
                role="RN",
                active=True,
            )
        )
        db_session.commit()


@pytest.fixture()
def document_storage_env(monkeypatch):
    root = (
        Path(__file__).resolve().parents[1]
        / "storage"
        / "test_documents_pytest"
        / uuid.uuid4().hex
    )
    monkeypatch.setenv("DOCUMENT_STORAGE_PROVIDER", "local")
    monkeypatch.setenv("DOCUMENT_STORAGE_DIR", str(root))
    monkeypatch.setenv("DOCUMENT_MAX_UPLOAD_BYTES", "1048576")
    get_document_storage.cache_clear()
    try:
        yield root
    finally:
        get_document_storage.cache_clear()
        shutil.rmtree(root, ignore_errors=True)


def _minimal_valid_pdf_bytes() -> bytes:
    """A real, parseable single-page PDF (not a fake header + text body).

    The upload endpoint (app/api/documents.py) opens every uploaded PDF with
    pypdf's PdfReader and rejects anything it can't parse (422 "Uploaded PDF
    could not be read") -- added 2026-08-26. A fake payload like
    b"%PDF-1.4\n...\n%%EOF" merely *looks* like a PDF by prefix/suffix; pypdf
    correctly refuses it. Build a genuinely valid minimal PDF via PdfWriter
    instead of hand-crafting byte offsets.
    """
    from io import BytesIO

    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buf = BytesIO()
    writer.write(buf)
    return buf.getvalue()


@pytest.mark.integration
def test_document_upload_list_and_download_round_trip(
    client, db_session, document_storage_env
):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)
    payload = _minimal_valid_pdf_bytes()

    upload_response = client.post(
        "/documents/",
        headers=_headers(TEST_USER_ID, "RN", tenant_id),
        data={
            "patient_id": str(patient.id),
            "document_type": "AUTHORIZATION",
            "source": "EXTERNAL",
        },
        files={"file": ("authorization.pdf", payload, "application/pdf")},
    )
    assert upload_response.status_code == 201, upload_response.text
    uploaded = upload_response.json()
    assert uploaded["document_id"]
    assert uploaded["file_name"] == "authorization.pdf"
    assert uploaded["size_bytes"] == len(payload)
    assert uploaded["content_type"] == "application/pdf"

    document_id = uploaded["document_id"]
    stored = db_session.get(DocumentRecord, uuid.UUID(document_id))
    assert stored is not None
    assert stored.file_name == "authorization.pdf"
    assert stored.file_path
    stored_path = document_storage_env / Path(*stored.file_path.split("/"))
    assert stored_path.read_bytes() == payload

    list_response = client.get(
        f"/documents/patient/{patient.id}",
        headers=_headers(TEST_USER_ID, "RN", tenant_id),
        params={"document_type": "AUTHORIZATION"},
    )
    assert list_response.status_code == 200, list_response.text
    listed = list_response.json()["documents"]
    assert len(listed) == 1
    assert listed[0]["id"] == document_id
    assert listed[0]["document_type"] == "AUTHORIZATION"
    assert listed[0]["file_name"] == "authorization.pdf"

    download_response = client.get(
        f"/documents/{document_id}/download",
        headers=_headers(TEST_USER_ID, "RN", tenant_id),
    )
    assert download_response.status_code == 200, download_response.text
    assert download_response.content == payload
    assert download_response.headers["content-type"].startswith("application/pdf")


@pytest.mark.integration
def test_document_upload_rejects_patient_outside_current_users_tenant(
    client, db_session, document_storage_env
):
    current_tenant_id = uuid.UUID(db_session.info["tenant_id"])
    other_tenant_id = uuid.uuid4()
    _ensure_tenant_and_user(db_session, other_tenant_id, uuid.uuid4())
    other_patient = _make_patient(db_session, other_tenant_id, mrn_prefix="XDOC")

    response = client.post(
        "/documents/",
        headers=_headers(TEST_USER_ID, "RN", current_tenant_id),
        data={
            "patient_id": str(other_patient.id),
            "document_type": "AUTHORIZATION",
        },
        files={"file": ("authorization.pdf", b"forbidden", "application/pdf")},
    )
    assert response.status_code == 404, response.text


@pytest.mark.integration
def test_document_download_rejects_cross_tenant_access(
    client, db_session, document_storage_env
):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)
    upload_response = client.post(
        "/documents/",
        headers=_headers(TEST_USER_ID, "RN", tenant_id),
        data={
            "patient_id": str(patient.id),
            "document_type": "ELIGIBILITY_SUBMISSION",
        },
        files={"file": ("eligibility.pdf", _minimal_valid_pdf_bytes(), "application/pdf")},
    )
    assert upload_response.status_code == 201, upload_response.text
    document_id = upload_response.json()["document_id"]

    other_tenant_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    _ensure_tenant_and_user(db_session, other_tenant_id, other_user_id)

    response = client.get(
        f"/documents/{document_id}/download",
        headers=_headers(other_user_id, "RN", other_tenant_id),
    )
    assert response.status_code == 404, response.text


@pytest.mark.integration
def test_document_upload_rejects_oversized_file(client, db_session, monkeypatch):
    tenant_id = uuid.UUID(db_session.info["tenant_id"])
    patient = _make_patient(db_session, tenant_id)
    storage_root = (
        Path(__file__).resolve().parents[1]
        / "storage"
        / "test_documents_pytest"
        / uuid.uuid4().hex
    )
    monkeypatch.setenv("DOCUMENT_STORAGE_PROVIDER", "local")
    monkeypatch.setenv("DOCUMENT_STORAGE_DIR", str(storage_root))
    monkeypatch.setenv("DOCUMENT_MAX_UPLOAD_BYTES", "5")
    get_document_storage.cache_clear()
    try:
        response = client.post(
            "/documents/",
            headers=_headers(TEST_USER_ID, "RN", tenant_id),
            data={
                "patient_id": str(patient.id),
                "document_type": "AUTHORIZATION",
            },
            files={"file": ("authorization.pdf", b"123456", "application/pdf")},
        )
        assert response.status_code == 413, response.text
        assert "maximum allowed size" in response.json()["detail"].lower()
    finally:
        get_document_storage.cache_clear()
        shutil.rmtree(storage_root, ignore_errors=True)
