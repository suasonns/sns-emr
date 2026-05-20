# app/services/survey_export.py

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session


def build_survey_export_zip(
    db: Optional[Session] = None,
    *,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    **kwargs: Any,
) -> bytes:
    """
    Build a survey export ZIP bundle.

    Enterprise-safe minimal implementation:
      - Returns a valid ZIP with a manifest.json.
      - Does NOT require DB access to function (startup-safe).
      - Allows survey endpoints to run without crashing while full export logic is implemented.

    This does NOT make clinical decisions. It is a packaging utility.
    """
    manifest: Dict[str, Any] = {
        "generated_at_utc": datetime.utcnow().isoformat() + "Z",
        "tenant_id": tenant_id,
        "user_id": user_id,
        "parameters": kwargs,
        "note": "Minimal export bundle (stub). Replace with full survey export content when ready.",
    }

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

    return buf.getvalue()