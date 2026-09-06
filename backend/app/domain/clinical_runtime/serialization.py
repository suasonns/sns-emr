# app/domain/clinical_runtime/serialization.py
"""
Safe JSON-serialization helper for clinical_runtime contracts.

Used when a contract needs to be persisted (e.g. as an audit-record payload)
or returned from an API. Converts dataclasses/enums/UUID/datetime into plain
JSON-safe primitives without relying on each contract implementing its own
ad-hoc serialization.

This does NOT redact clinical values -- callers that persist or transmit the
serialized payload are responsible for applying their own PHI-handling
policy (e.g. encryption at rest, access controls on the audit-log table).
This module's only job is deterministic, lossless-for-JSON conversion.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID


def to_serializable(value: Any) -> Any:
    """Recursively convert a contract (or nested value) into JSON-safe primitives."""

    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            f.name: to_serializable(getattr(value, f.name))
            for f in dataclasses.fields(value)
        }
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError(f"Cannot serialize naive datetime: {value!r}")
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, dict):
        return {k: to_serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_serializable(v) for v in value]
    return value
