from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Protocol, runtime_checkable


DEFAULT_MAX_UPLOAD_BYTES = 250 * 1024 * 1024
DEFAULT_STORAGE_ROOT = Path(__file__).resolve().parents[2] / "storage" / "visit_recordings"
MIME_TYPE_EXTENSIONS = {
    "audio/mp4": "m4a",
    "audio/mpeg": "mp3",
    "audio/ogg": "ogg",
    "audio/wav": "wav",
    "audio/webm": "webm",
    "audio/x-m4a": "m4a",
    "audio/x-wav": "wav",
}


class RecordingStorageError(RuntimeError):
    """Base exception for recording object operations."""


class InvalidRecordingKey(RecordingStorageError):
    pass


class RecordingObjectNotFound(RecordingStorageError):
    pass


class RecordingUploadTooLarge(RecordingStorageError):
    pass


class RecordingRangeNotSatisfiable(RecordingStorageError):
    def __init__(self, total_length: int) -> None:
        super().__init__("Requested recording range is not satisfiable")
        self.total_length = total_length


class RecordingStorageConfigurationError(RecordingStorageError):
    pass


@dataclass(frozen=True)
class RecordingObject:
    body: BinaryIO
    content_length: int
    total_length: int
    range_start: int
    range_end: int


@runtime_checkable
class RecordingStorageProvider(Protocol):
    def put(
        self,
        key: str,
        source: BinaryIO,
        *,
        content_type: str,
        max_bytes: int,
    ) -> int: ...

    def open(self, key: str, range_header: str | None = None) -> RecordingObject: ...

    def delete(self, key: str) -> bool: ...


def normalize_recording_mime_type(content_type: str | None) -> str:
    normalized = (content_type or "").split(";", 1)[0].strip().lower()
    if normalized not in MIME_TYPE_EXTENSIONS:
        raise ValueError("Unsupported recording MIME type")
    return normalized


def build_recording_key(
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    recording_id: uuid.UUID,
    content_type: str,
) -> str:
    extension = MIME_TYPE_EXTENSIONS[normalize_recording_mime_type(content_type)]
    return validate_recording_key(
        f"{tenant_id}/{patient_id}/{recording_id}.{extension}"
    )


def validate_recording_key(key: str) -> str:
    if not key or "\\" in key or "\x00" in key:
        raise InvalidRecordingKey("Recording key is invalid")
    path = PurePosixPath(key)
    if path.is_absolute() or len(path.parts) != 3:
        raise InvalidRecordingKey("Recording key must have three relative segments")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise InvalidRecordingKey("Recording key contains an unsafe segment")
    try:
        uuid.UUID(path.parts[0])
        uuid.UUID(path.parts[1])
        uuid.UUID(path.stem)
    except ValueError as exc:
        raise InvalidRecordingKey("Recording key contains an invalid identifier") from exc
    if path.suffix.lstrip(".") not in set(MIME_TYPE_EXTENSIONS.values()):
        raise InvalidRecordingKey("Recording key has an unsupported extension")
    return path.as_posix()


def max_upload_bytes_from_env() -> int:
    raw_value = os.getenv(
        "VISIT_RECORDING_MAX_UPLOAD_BYTES",
        str(DEFAULT_MAX_UPLOAD_BYTES),
    )
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RecordingStorageConfigurationError(
            "VISIT_RECORDING_MAX_UPLOAD_BYTES must be an integer"
        ) from exc
    if value <= 0:
        raise RecordingStorageConfigurationError(
            "VISIT_RECORDING_MAX_UPLOAD_BYTES must be greater than zero"
        )
    return value


class _LimitedReader:
    def __init__(self, source: BinaryIO, max_bytes: int) -> None:
        self._source = source
        self._max_bytes = max_bytes
        self.bytes_read = 0

    def read(self, size: int = -1) -> bytes:
        remaining = self._max_bytes - self.bytes_read
        requested = remaining + 1 if size < 0 else min(size, remaining + 1)
        data = self._source.read(requested)
        self.bytes_read += len(data)
        if self.bytes_read > self._max_bytes:
            raise RecordingUploadTooLarge("Recording exceeds maximum allowed size")
        return data


class _RangeReader:
    def __init__(self, source: BinaryIO, remaining: int) -> None:
        self._source = source
        self._remaining = remaining

    def read(self, size: int = -1) -> bytes:
        if self._remaining == 0:
            return b""
        requested = self._remaining if size < 0 else min(size, self._remaining)
        data = self._source.read(requested)
        self._remaining -= len(data)
        return data

    def close(self) -> None:
        self._source.close()


def _parse_range(range_header: str | None, total_length: int) -> tuple[int, int]:
    if not range_header:
        return 0, max(total_length - 1, 0)
    if not range_header.startswith("bytes=") or "," in range_header:
        raise RecordingRangeNotSatisfiable(total_length)
    start_text, separator, end_text = range_header[6:].partition("-")
    if not separator:
        raise RecordingRangeNotSatisfiable(total_length)
    try:
        if start_text:
            start = int(start_text)
            end = int(end_text) if end_text else total_length - 1
        else:
            suffix_length = int(end_text)
            if suffix_length <= 0:
                raise ValueError
            start = max(total_length - suffix_length, 0)
            end = total_length - 1
    except ValueError as exc:
        raise RecordingRangeNotSatisfiable(total_length) from exc
    if start < 0 or start >= total_length or end < start:
        raise RecordingRangeNotSatisfiable(total_length)
    return start, min(end, total_length - 1)


class LocalRecordingStorage:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, key: str) -> Path:
        safe_key = validate_recording_key(key)
        path = (self.root / Path(*PurePosixPath(safe_key).parts)).resolve()
        root = self.root.resolve()
        if path != root and root not in path.parents:
            raise InvalidRecordingKey("Recording key escapes the storage root")
        return path

    def put(
        self,
        key: str,
        source: BinaryIO,
        *,
        content_type: str,
        max_bytes: int,
    ) -> int:
        normalize_recording_mime_type(content_type)
        path = self._path(key)
        temporary_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        reader = _LimitedReader(source, max_bytes)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with temporary_path.open("wb") as target:
                while chunk := reader.read(1024 * 1024):
                    target.write(chunk)
            os.replace(temporary_path, path)
        except RecordingUploadTooLarge:
            temporary_path.unlink(missing_ok=True)
            raise
        except OSError as exc:
            temporary_path.unlink(missing_ok=True)
            raise RecordingStorageError("Failed to store recording object") from exc
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise
        return reader.bytes_read

    def open(self, key: str, range_header: str | None = None) -> RecordingObject:
        path = self._path(key)
        try:
            total_length = path.stat().st_size
            start, end = _parse_range(range_header, total_length)
            body = path.open("rb")
            body.seek(start)
            return RecordingObject(
                body=_RangeReader(body, end - start + 1),
                content_length=end - start + 1,
                total_length=total_length,
                range_start=start,
                range_end=end,
            )
        except FileNotFoundError as exc:
            raise RecordingObjectNotFound("Recording object was not found") from exc
        except OSError as exc:
            raise RecordingStorageError("Failed to read recording object") from exc

    def delete(self, key: str) -> bool:
        path = self._path(key)
        try:
            path.unlink()
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise RecordingStorageError("Failed to delete recording object") from exc
        return True


class S3RecordingStorage:
    def __init__(self, *, bucket: str, client: object) -> None:
        self.bucket = bucket
        self.client = client

    def put(
        self,
        key: str,
        source: BinaryIO,
        *,
        content_type: str,
        max_bytes: int,
    ) -> int:
        safe_key = validate_recording_key(key)
        normalized_type = normalize_recording_mime_type(content_type)
        reader = _LimitedReader(source, max_bytes)
        try:
            from boto3.s3.transfer import TransferConfig

            self.client.upload_fileobj(
                reader,
                self.bucket,
                safe_key,
                ExtraArgs={"ContentType": normalized_type},
                Config=TransferConfig(use_threads=False),
            )
        except RecordingUploadTooLarge:
            raise
        except Exception as exc:
            raise RecordingStorageError("Failed to store recording object") from exc
        return reader.bytes_read

    def open(self, key: str, range_header: str | None = None) -> RecordingObject:
        safe_key = validate_recording_key(key)
        try:
            metadata = self.client.head_object(Bucket=self.bucket, Key=safe_key)
        except Exception as exc:
            if _is_s3_missing_object(exc):
                raise RecordingObjectNotFound("Recording object was not found") from exc
            raise RecordingStorageError("Failed to read recording object") from exc
        total_length = int(metadata["ContentLength"])
        start, end = _parse_range(range_header, total_length)
        request = {"Bucket": self.bucket, "Key": safe_key}
        if range_header:
            request["Range"] = f"bytes={start}-{end}"
        try:
            response = self.client.get_object(**request)
        except Exception as exc:
            if _is_s3_missing_object(exc):
                raise RecordingObjectNotFound("Recording object was not found") from exc
            raise RecordingStorageError("Failed to read recording object") from exc
        return RecordingObject(
            body=response["Body"],
            content_length=end - start + 1,
            total_length=total_length,
            range_start=start,
            range_end=end,
        )

    def delete(self, key: str) -> bool:
        safe_key = validate_recording_key(key)
        try:
            self.client.head_object(Bucket=self.bucket, Key=safe_key)
        except Exception as exc:
            if _is_s3_missing_object(exc):
                return False
            raise RecordingStorageError("Failed to inspect recording object") from exc
        try:
            self.client.delete_object(Bucket=self.bucket, Key=safe_key)
        except Exception as exc:
            raise RecordingStorageError("Failed to delete recording object") from exc
        return True


def _is_s3_missing_object(exc: Exception) -> bool:
    response = getattr(exc, "response", {})
    error = response.get("Error", {}) if isinstance(response, dict) else {}
    return str(error.get("Code", "")) in {"404", "NoSuchKey", "NotFound"}


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RecordingStorageConfigurationError(f"{name} is required for S3 storage")
    return value


@lru_cache(maxsize=1)
def get_recording_storage() -> RecordingStorageProvider:
    provider = os.getenv("VISIT_RECORDING_STORAGE_PROVIDER", "local").strip().lower()
    if provider == "local":
        root = Path(os.getenv("VISIT_RECORDING_STORAGE_DIR", str(DEFAULT_STORAGE_ROOT)))
        return LocalRecordingStorage(root)
    if provider == "s3":
        import boto3
        from botocore.config import Config

        client = boto3.client(
            "s3",
            endpoint_url=_required_env("VISIT_RECORDING_S3_ENDPOINT"),
            region_name=_required_env("VISIT_RECORDING_S3_REGION"),
            aws_access_key_id=_required_env("VISIT_RECORDING_S3_ACCESS_KEY"),
            aws_secret_access_key=_required_env("VISIT_RECORDING_S3_SECRET_KEY"),
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "virtual"},
            ),
        )
        return S3RecordingStorage(
            bucket=_required_env("VISIT_RECORDING_S3_BUCKET"),
            client=client,
        )
    raise RecordingStorageConfigurationError(
        "VISIT_RECORDING_STORAGE_PROVIDER must be 'local' or 's3'"
    )
