from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Protocol, runtime_checkable


DEFAULT_MAX_UPLOAD_BYTES = 50 * 1024 * 1024
DEFAULT_STORAGE_ROOT = Path(__file__).resolve().parents[2] / "storage" / "documents"
MIME_TYPE_EXTENSIONS = {
    "application/msword": "doc",
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/tiff": "tiff",
    "text/plain": "txt",
}
EXTENSION_MIME_TYPES = {
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "pdf": "application/pdf",
    "png": "image/png",
    "tif": "image/tiff",
    "tiff": "image/tiff",
    "txt": "text/plain",
}


class DocumentStorageError(RuntimeError):
    """Base exception for document object operations."""


class InvalidDocumentKey(DocumentStorageError):
    pass


class DocumentObjectNotFound(DocumentStorageError):
    pass


class DocumentUploadTooLarge(DocumentStorageError):
    pass


class DocumentRangeNotSatisfiable(DocumentStorageError):
    def __init__(self, total_length: int) -> None:
        super().__init__("Requested document range is not satisfiable")
        self.total_length = total_length


class DocumentStorageConfigurationError(DocumentStorageError):
    pass


@dataclass(frozen=True)
class DocumentObject:
    body: BinaryIO
    content_length: int
    total_length: int
    range_start: int
    range_end: int


@runtime_checkable
class DocumentStorageProvider(Protocol):
    def put(
        self,
        key: str,
        source: BinaryIO,
        *,
        content_type: str,
        max_bytes: int,
    ) -> int: ...

    def open(self, key: str, range_header: str | None = None) -> DocumentObject: ...

    def delete(self, key: str) -> bool: ...


def normalize_document_mime_type(
    content_type: str | None,
    *,
    filename: str | None = None,
) -> str:
    normalized = (content_type or "").split(";", 1)[0].strip().lower()
    if normalized in MIME_TYPE_EXTENSIONS:
        return normalized
    extension = _extension_from_filename(filename)
    if extension and extension in EXTENSION_MIME_TYPES:
        return EXTENSION_MIME_TYPES[extension]
    raise ValueError("Unsupported document MIME type")


def build_document_key(
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    document_id: uuid.UUID,
    content_type: str,
) -> str:
    extension = MIME_TYPE_EXTENSIONS[normalize_document_mime_type(content_type)]
    return validate_document_key(f"{tenant_id}/{patient_id}/{document_id}.{extension}")


def validate_document_key(key: str) -> str:
    if not key or "\\" in key or "\x00" in key:
        raise InvalidDocumentKey("Document key is invalid")
    path = PurePosixPath(key)
    if path.is_absolute() or len(path.parts) != 3:
        raise InvalidDocumentKey("Document key must have three relative segments")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise InvalidDocumentKey("Document key contains an unsafe segment")
    try:
        uuid.UUID(path.parts[0])
        uuid.UUID(path.parts[1])
        uuid.UUID(path.stem)
    except ValueError as exc:
        raise InvalidDocumentKey("Document key contains an invalid identifier") from exc
    if path.suffix.lstrip(".").lower() not in set(EXTENSION_MIME_TYPES):
        raise InvalidDocumentKey("Document key has an unsupported extension")
    return path.as_posix()


def guess_document_content_type(
    *,
    file_name: str | None = None,
    file_path: str | None = None,
) -> str:
    extension = _extension_from_filename(file_name)
    if not extension and file_path:
        extension = PurePosixPath(file_path).suffix.lstrip(".").lower()
    return EXTENSION_MIME_TYPES.get(extension or "", "application/octet-stream")


def max_upload_bytes_from_env() -> int:
    raw_value = os.getenv("DOCUMENT_MAX_UPLOAD_BYTES", str(DEFAULT_MAX_UPLOAD_BYTES))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise DocumentStorageConfigurationError(
            "DOCUMENT_MAX_UPLOAD_BYTES must be an integer"
        ) from exc
    if value <= 0:
        raise DocumentStorageConfigurationError(
            "DOCUMENT_MAX_UPLOAD_BYTES must be greater than zero"
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
            raise DocumentUploadTooLarge("Document exceeds maximum allowed size")
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
        raise DocumentRangeNotSatisfiable(total_length)
    start_text, separator, end_text = range_header[6:].partition("-")
    if not separator:
        raise DocumentRangeNotSatisfiable(total_length)
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
        raise DocumentRangeNotSatisfiable(total_length) from exc
    if start < 0 or start >= total_length or end < start:
        raise DocumentRangeNotSatisfiable(total_length)
    return start, min(end, total_length - 1)


class LocalDocumentStorage:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, key: str) -> Path:
        safe_key = validate_document_key(key)
        path = (self.root / Path(*PurePosixPath(safe_key).parts)).resolve()
        root = self.root.resolve()
        if path != root and root not in path.parents:
            raise InvalidDocumentKey("Document key escapes the storage root")
        return path

    def put(
        self,
        key: str,
        source: BinaryIO,
        *,
        content_type: str,
        max_bytes: int,
    ) -> int:
        normalize_document_mime_type(content_type)
        path = self._path(key)
        temporary_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        reader = _LimitedReader(source, max_bytes)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with temporary_path.open("wb") as target:
                while chunk := reader.read(1024 * 1024):
                    target.write(chunk)
            os.replace(temporary_path, path)
        except DocumentUploadTooLarge:
            temporary_path.unlink(missing_ok=True)
            raise
        except OSError as exc:
            temporary_path.unlink(missing_ok=True)
            raise DocumentStorageError("Failed to store document object") from exc
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise
        return reader.bytes_read

    def open(self, key: str, range_header: str | None = None) -> DocumentObject:
        path = self._path(key)
        try:
            total_length = path.stat().st_size
            start, end = _parse_range(range_header, total_length)
            body = path.open("rb")
            body.seek(start)
            return DocumentObject(
                body=_RangeReader(body, end - start + 1),
                content_length=end - start + 1,
                total_length=total_length,
                range_start=start,
                range_end=end,
            )
        except FileNotFoundError as exc:
            raise DocumentObjectNotFound("Document object was not found") from exc
        except OSError as exc:
            raise DocumentStorageError("Failed to read document object") from exc

    def delete(self, key: str) -> bool:
        path = self._path(key)
        try:
            path.unlink()
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise DocumentStorageError("Failed to delete document object") from exc
        return True


class S3DocumentStorage:
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
        safe_key = validate_document_key(key)
        normalized_type = normalize_document_mime_type(content_type)
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
        except DocumentUploadTooLarge:
            raise
        except Exception as exc:
            raise DocumentStorageError("Failed to store document object") from exc
        return reader.bytes_read

    def open(self, key: str, range_header: str | None = None) -> DocumentObject:
        safe_key = validate_document_key(key)
        try:
            metadata = self.client.head_object(Bucket=self.bucket, Key=safe_key)
        except Exception as exc:
            if _is_s3_missing_object(exc):
                raise DocumentObjectNotFound("Document object was not found") from exc
            raise DocumentStorageError("Failed to read document object") from exc
        total_length = int(metadata["ContentLength"])
        start, end = _parse_range(range_header, total_length)
        request = {"Bucket": self.bucket, "Key": safe_key}
        if range_header:
            request["Range"] = f"bytes={start}-{end}"
        try:
            response = self.client.get_object(**request)
        except Exception as exc:
            if _is_s3_missing_object(exc):
                raise DocumentObjectNotFound("Document object was not found") from exc
            raise DocumentStorageError("Failed to read document object") from exc
        return DocumentObject(
            body=response["Body"],
            content_length=end - start + 1,
            total_length=total_length,
            range_start=start,
            range_end=end,
        )

    def delete(self, key: str) -> bool:
        safe_key = validate_document_key(key)
        try:
            self.client.head_object(Bucket=self.bucket, Key=safe_key)
        except Exception as exc:
            if _is_s3_missing_object(exc):
                return False
            raise DocumentStorageError("Failed to inspect document object") from exc
        try:
            self.client.delete_object(Bucket=self.bucket, Key=safe_key)
        except Exception as exc:
            raise DocumentStorageError("Failed to delete document object") from exc
        return True


def _extension_from_filename(filename: str | None) -> str | None:
    if not filename:
        return None
    suffix = Path(filename).suffix.lstrip(".").lower()
    return suffix or None


def _is_s3_missing_object(exc: Exception) -> bool:
    response = getattr(exc, "response", {})
    error = response.get("Error", {}) if isinstance(response, dict) else {}
    return str(error.get("Code", "")) in {"404", "NoSuchKey", "NotFound"}


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise DocumentStorageConfigurationError(f"{name} is required for S3 storage")
    return value


@lru_cache(maxsize=1)
def get_document_storage() -> DocumentStorageProvider:
    provider = os.getenv("DOCUMENT_STORAGE_PROVIDER", "local").strip().lower()
    if provider == "local":
        root = Path(os.getenv("DOCUMENT_STORAGE_DIR", str(DEFAULT_STORAGE_ROOT)))
        return LocalDocumentStorage(root)
    if provider == "s3":
        import boto3
        from botocore.config import Config

        client = boto3.client(
            "s3",
            endpoint_url=_required_env("DOCUMENT_S3_ENDPOINT"),
            region_name=_required_env("DOCUMENT_S3_REGION"),
            aws_access_key_id=_required_env("DOCUMENT_S3_ACCESS_KEY"),
            aws_secret_access_key=_required_env("DOCUMENT_S3_SECRET_KEY"),
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "virtual"},
            ),
        )
        return S3DocumentStorage(
            bucket=_required_env("DOCUMENT_S3_BUCKET"),
            client=client,
        )
    raise DocumentStorageConfigurationError(
        "DOCUMENT_STORAGE_PROVIDER must be 'local' or 's3'"
    )
