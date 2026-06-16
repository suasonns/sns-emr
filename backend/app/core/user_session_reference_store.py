from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any, Optional


_STORE: dict[str, "UserSessionReferenceRecord"] = {}
_LOCK = Lock()
DEFAULT_TTL_MINUTES = 60


@dataclass
class UserSessionReferenceRecord:
    ref: str
    user_id: str
    role: str
    tenant_id: str | None
    created_at: str
    expires_at: str
    ui_context: dict[str, Any]


def put_user_session_reference(
    *,
    ref: str,
    user_id: str,
    role: str,
    tenant_id: str | None,
    ui_context: Optional[dict[str, Any]] = None,
    ttl_minutes: int = DEFAULT_TTL_MINUTES,
) -> None:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=ttl_minutes)

    record = UserSessionReferenceRecord(
        ref=ref,
        user_id=str(user_id),
        role=str(role),
        tenant_id=str(tenant_id) if tenant_id else None,
        created_at=now.isoformat(),
        expires_at=exp.isoformat(),
        ui_context=ui_context or {},
    )

    with _LOCK:
        _cleanup_locked(now)
        _STORE[ref] = record


def get_user_session_reference(ref: str) -> Optional[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    with _LOCK:
        _cleanup_locked(now)
        record = _STORE.get(ref)
        return asdict(record) if record else None


def _cleanup_locked(now: datetime) -> None:
    expired = []
    for k, v in _STORE.items():
        try:
            expires = datetime.fromisoformat(v.expires_at)
        except Exception:
            expired.append(k)
            continue
        if expires <= now:
            expired.append(k)
    for k in expired:
        _STORE.pop(k, None)