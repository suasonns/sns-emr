from __future__ import annotations

import io
import uuid

import pytest
from botocore.exceptions import ClientError

from app.services.recording_storage import (
    InvalidRecordingKey,
    LocalRecordingStorage,
    RecordingObjectNotFound,
    RecordingRangeNotSatisfiable,
    RecordingUploadTooLarge,
    S3RecordingStorage,
    build_recording_key,
    normalize_recording_mime_type,
    validate_recording_key,
)


TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
PATIENT_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
RECORDING_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")


def _key() -> str:
    return build_recording_key(
        tenant_id=TENANT_ID,
        patient_id=PATIENT_ID,
        recording_id=RECORDING_ID,
        content_type="audio/webm",
    )


def test_local_provider_round_trip_and_delete(tmp_path):
    storage = LocalRecordingStorage(tmp_path)

    size = storage.put(
        _key(),
        io.BytesIO(b"private audio"),
        content_type="audio/webm",
        max_bytes=100,
    )

    stored = storage.open(_key())
    assert size == 13
    assert stored.body.read() == b"private audio"
    stored.body.close()
    ranged = storage.open(_key(), "bytes=2-8")
    assert ranged.body.read() == b"ivate a"
    assert ranged.content_length == 7
    assert ranged.total_length == 13
    ranged.body.close()
    with pytest.raises(RecordingRangeNotSatisfiable):
        storage.open(_key(), "bytes=99-100")
    assert storage.delete(_key()) is True
    assert storage.delete(_key()) is False
    with pytest.raises(RecordingObjectNotFound):
        storage.open(_key())


def test_local_provider_removes_partial_file_when_upload_exceeds_limit(tmp_path):
    storage = LocalRecordingStorage(tmp_path)

    with pytest.raises(RecordingUploadTooLarge):
        storage.put(
            _key(),
            io.BytesIO(b"123456"),
            content_type="audio/webm",
            max_bytes=5,
        )

    with pytest.raises(RecordingObjectNotFound):
        storage.open(_key())
    assert list(tmp_path.rglob("*.tmp")) == []


@pytest.mark.parametrize(
    "unsafe_key",
    [
        "../patient/recording.webm",
        f"{TENANT_ID}/../{RECORDING_ID}.webm",
        f"{TENANT_ID}\\{PATIENT_ID}\\{RECORDING_ID}.webm",
        f"/{TENANT_ID}/{PATIENT_ID}/{RECORDING_ID}.webm",
        f"{TENANT_ID}/{PATIENT_ID}/not-a-uuid.webm",
    ],
)
def test_key_validation_rejects_traversal_and_non_generated_keys(unsafe_key):
    with pytest.raises(InvalidRecordingKey):
        validate_recording_key(unsafe_key)


def test_mime_validation_rejects_non_audio_and_normalizes_parameters():
    assert normalize_recording_mime_type("audio/webm; codecs=opus") == "audio/webm"
    with pytest.raises(ValueError, match="Unsupported"):
        normalize_recording_mime_type("text/html")


class _FakeS3Client:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.upload_args = None

    def upload_fileobj(self, source, bucket, key, **kwargs):
        self.upload_args = (bucket, key, kwargs)
        self.objects[key] = source.read()

    def get_object(self, *, Bucket, Key):
        if Key not in self.objects:
            raise _missing_object_error()
        data = self.objects[Key]
        return {"Body": io.BytesIO(data), "ContentLength": len(data)}

    def head_object(self, *, Bucket, Key):
        if Key not in self.objects:
            raise _missing_object_error()
        return {"ContentLength": len(self.objects[Key])}

    def delete_object(self, *, Bucket, Key):
        self.objects.pop(Key, None)


def _missing_object_error() -> ClientError:
    return ClientError({"Error": {"Code": "404", "Message": "missing"}}, "GetObject")


def test_s3_provider_uses_private_object_calls_and_handles_missing_objects():
    client = _FakeS3Client()
    storage = S3RecordingStorage(bucket="private-recordings", client=client)

    assert storage.put(
        _key(),
        io.BytesIO(b"cloud audio"),
        content_type="audio/webm",
        max_bytes=100,
    ) == 11
    bucket, key, kwargs = client.upload_args
    assert bucket == "private-recordings"
    assert key == _key()
    assert kwargs["ExtraArgs"] == {"ContentType": "audio/webm"}
    assert "ACL" not in kwargs["ExtraArgs"]
    assert storage.open(_key()).body.read() == b"cloud audio"
    assert storage.delete(_key()) is True
    assert storage.delete(_key()) is False
    with pytest.raises(RecordingObjectNotFound):
        storage.open(_key())
