from __future__ import annotations

import asyncio
import io
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks, HTTPException, UploadFile
from starlette.requests import Request

from app.api import visit_recordings
from app.core.security import CurrentUser
from app.services.recording_storage import (
    RecordingObjectNotFound,
    RecordingUploadTooLarge,
)


TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
PATIENT_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
RECORDING_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
USER_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")
USER = CurrentUser(user_id=USER_ID, role="RN", tenant_id=TENANT_ID)


class _Query:
    def __init__(self, row):
        self.row = row

    def filter(self, *args):
        return self

    def one_or_none(self):
        return self.row


class _Db:
    def __init__(self, row=None, *, fail_commit=False):
        self.row = row
        self.fail_commit = fail_commit
        self.added = None
        self.rolled_back = False

    def query(self, model):
        return _Query(self.row)

    def add(self, row):
        self.added = row

    def commit(self):
        if self.fail_commit:
            raise RuntimeError("database unavailable")

    def refresh(self, row):
        return None

    def rollback(self):
        self.rolled_back = True


class _Storage:
    def __init__(self, *, put_error=None, missing=False):
        self.put_error = put_error
        self.missing = missing
        self.put_calls = []
        self.deleted = []

    def put(self, key, source, *, content_type, max_bytes):
        self.put_calls.append((key, content_type, max_bytes))
        if self.put_error:
            raise self.put_error
        return len(source.read())

    def open(self, key, range_header=None):
        if self.missing:
            raise RecordingObjectNotFound("missing")
        raise AssertionError("not used")

    def delete(self, key):
        self.deleted.append(key)
        return True


def _recording():
    return SimpleNamespace(
        id=RECORDING_ID,
        patient_id=PATIENT_ID,
        deleted_at=None,
        deleted_by=None,
        file_path=f"{TENANT_ID}/{PATIENT_ID}/{RECORDING_ID}.webm",
        mime_type="audio/webm",
        file_name="visit.webm",
    )


def test_owned_recording_preserves_patient_access_control(monkeypatch):
    expected = HTTPException(status_code=404, detail="Patient not found")

    def deny_access(*args, **kwargs):
        raise expected

    monkeypatch.setattr(visit_recordings, "get_authorized_patient", deny_access)
    with pytest.raises(HTTPException) as exc_info:
        visit_recordings._get_owned_recording(_Db(_recording()), RECORDING_ID, USER)
    assert exc_info.value is expected


def test_upload_rejects_unsupported_mime_before_storage(monkeypatch):
    monkeypatch.setattr(
        visit_recordings,
        "get_authorized_patient",
        lambda *args: SimpleNamespace(id=PATIENT_ID, tenant_id=TENANT_ID),
    )
    storage = _Storage()
    upload = UploadFile(filename="visit.txt", file=io.BytesIO(b"not audio"))

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            visit_recordings.upload_recording(
                patient_id=PATIENT_ID,
                consent_confirmed=True,
                audio=upload,
                db=_Db(),
                current_user=USER,
                storage=storage,
                background_tasks=BackgroundTasks(),
            )
        )

    assert exc_info.value.status_code == 415
    assert storage.put_calls == []


def test_upload_limit_error_is_explicit(monkeypatch):
    monkeypatch.setattr(
        visit_recordings,
        "get_authorized_patient",
        lambda *args: SimpleNamespace(id=PATIENT_ID, tenant_id=TENANT_ID),
    )
    storage = _Storage(
        put_error=RecordingUploadTooLarge("Recording exceeds maximum allowed size")
    )
    upload = UploadFile(
        filename="visit.webm",
        file=io.BytesIO(b"too large"),
        headers={"content-type": "audio/webm"},
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            visit_recordings.upload_recording(
                patient_id=PATIENT_ID,
                consent_confirmed=True,
                audio=upload,
                db=_Db(),
                current_user=USER,
                storage=storage,
                background_tasks=BackgroundTasks(),
            )
        )
    assert exc_info.value.status_code == 413


def test_database_failure_rolls_back_and_removes_uploaded_object(monkeypatch):
    monkeypatch.setattr(
        visit_recordings,
        "get_authorized_patient",
        lambda *args: SimpleNamespace(id=PATIENT_ID, tenant_id=TENANT_ID),
    )
    db = _Db(fail_commit=True)
    storage = _Storage()
    upload = UploadFile(
        filename="visit.webm",
        file=io.BytesIO(b"audio"),
        headers={"content-type": "audio/webm"},
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            visit_recordings.upload_recording(
                patient_id=PATIENT_ID,
                consent_confirmed=True,
                audio=upload,
                db=db,
                current_user=USER,
                storage=storage,
                background_tasks=BackgroundTasks(),
            )
        )

    assert exc_info.value.status_code == 500
    assert db.rolled_back is True
    assert storage.deleted == [db.added.file_path]


def test_playback_reports_missing_private_object(monkeypatch):
    rec = _recording()
    monkeypatch.setattr(
        visit_recordings,
        "_get_owned_recording",
        lambda *args: rec,
    )

    with pytest.raises(HTTPException) as exc_info:
        visit_recordings.stream_recording_audio(
            RECORDING_ID,
            request=Request({"type": "http", "headers": []}),
            db=_Db(rec),
            current_user=USER,
            storage=_Storage(missing=True),
        )
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Recording object missing from storage"


def test_delete_is_retention_preserving_soft_delete(monkeypatch):
    rec = _recording()
    monkeypatch.setattr(
        visit_recordings,
        "_get_owned_recording",
        lambda *args: rec,
    )
    db = _Db(rec)

    result = visit_recordings.soft_delete_recording(
        RECORDING_ID,
        db=db,
        current_user=USER,
    )

    assert result == {"status": "deleted", "id": str(RECORDING_ID)}
    assert rec.deleted_by == USER_ID
    assert isinstance(rec.deleted_at, datetime)
    assert rec.deleted_at.tzinfo == timezone.utc
