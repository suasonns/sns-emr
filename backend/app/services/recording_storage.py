from __future__ import annotations

"""
Local-disk storage for visit audio recordings.

Kept intentionally simple (no cloud bucket, no third-party dependency) since
we're building the capture + review pipeline before deciding/wiring the
speech-to-text vendor. Paths are always built from server-generated UUIDs and
a whitelisted extension, never from user-controlled strings, so there is no
path-traversal surface even though this resolves real filesystem paths.
"""

import os
import uuid
from pathlib import Path
from typing import BinaryIO

# Root directory for stored recordings. Configurable via env var so
# deployments can point this at a mounted volume; defaults to a folder next
# to the backend app that is git-ignored (never committed alongside code).
STORAGE_ROOT = Path(os.getenv("VISIT_RECORDING_STORAGE_DIR", str(Path(__file__).resolve().parents[2] / "storage" / "visit_recordings")))

ALLOWED_EXTENSIONS = {"webm", "ogg", "mp3", "wav", "m4a"}
DEFAULT_EXTENSION = "webm"


def _safe_extension(mime_type: str | None, file_name: str | None) -> str:
    if file_name and "." in file_name:
        ext = file_name.rsplit(".", 1)[-1].lower()
        if ext in ALLOWED_EXTENSIONS:
            return ext
    if mime_type:
        guess = mime_type.split("/")[-1].split(";")[0].strip().lower()
        if guess in ALLOWED_EXTENSIONS:
            return guess
        if guess == "mpeg":
            return "mp3"
    return DEFAULT_EXTENSION


def build_recording_path(tenant_id: uuid.UUID, patient_id: uuid.UUID, recording_id: uuid.UUID, mime_type: str | None, file_name: str | None) -> tuple[Path, str]:
    """Returns (absolute_path, relative_path_to_store_in_db)."""
    ext = _safe_extension(mime_type, file_name)
    relative = Path(str(tenant_id)) / str(patient_id) / f"{recording_id}.{ext}"
    absolute = STORAGE_ROOT / relative
    return absolute, str(relative)


def save_recording_bytes(absolute_path: Path, data: bytes) -> int:
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    with open(absolute_path, "wb") as f:
        f.write(data)
    return len(data)


async def save_recording_stream(absolute_path: Path, stream: BinaryIO) -> int:
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    size = 0
    with open(absolute_path, "wb") as out:
        while True:
            chunk = await stream.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            size += len(chunk)
    return size


def resolve_recording_path(relative_path: str) -> Path:
    """Resolve a DB-stored relative path back to an absolute path, with a
    belt-and-suspenders check that it can't escape STORAGE_ROOT."""
    absolute = (STORAGE_ROOT / relative_path).resolve()
    root_resolved = STORAGE_ROOT.resolve()
    if root_resolved not in absolute.parents and absolute != root_resolved:
        raise ValueError("Resolved recording path escapes storage root")
    return absolute


def delete_recording_file(relative_path: str) -> None:
    try:
        path = resolve_recording_path(relative_path)
        if path.exists():
            path.unlink()
    except ValueError:
        pass
