# app/services/fax_service.py

"""
Fax transmission service for hospice orders (physician orders, comfort packs,
DME/supply requests) sent to a pharmacy, DME vendor, or physician office.

Architecture:
- Pluggable provider interface, same pattern as drug_safety_service.py's
  curated-JSON-now/licensed-feed-later design: a real fax gateway (SRFax,
  Sfax, Phaxio/Sinch, etc.) can be wired in later by adding a new provider
  function and switching FAX_PROVIDER, without changing any caller code.
- Today's default provider is "SIMULATED": it logs the fax request, builds
  a printable/faxable document summary, and marks the record QUEUED. This
  gives the agency a complete, auditable fax queue/history feature (matching
  HospiceMD's "Fax Order/History" and "Fax Tx/Med/DME / History" screens)
  without requiring a paid fax API account before go-live.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.fax_log import FaxLog

logger = logging.getLogger("fax")

FAX_PROVIDER = "SIMULATED"


def _simulated_send(recipient_fax_number: str, document_summary: str) -> tuple[str, str, Optional[str]]:
    """
    Simulated fax transmission. Returns (status, provider_reference, failure_reason).

    Swap this out for a real gateway call (e.g. SRFax `Queue_Fax`, Sfax API,
    Phaxio `send`) when a fax provider account is available — the rest of
    the service (FaxLog persistence, audit logging, API surface) stays the
    same.
    """
    if not recipient_fax_number or not recipient_fax_number.strip():
        return "FAILED", None, "No fax number on file for recipient."

    reference = f"SIM-{uuid.uuid4().hex[:10].upper()}"
    logger.info(
        "[FAX-SIMULATED] queued fax to %s ref=%s (%d chars)",
        recipient_fax_number,
        reference,
        len(document_summary or ""),
    )
    return "QUEUED", reference, None


def send_fax(
    db: Session,
    *,
    tenant_id,
    patient_id,
    subject_type: str,
    subject_id: Optional[uuid.UUID],
    recipient_name: str,
    recipient_fax_number: str,
    document_summary: str,
    created_by=None,
) -> FaxLog:
    if FAX_PROVIDER == "SIMULATED":
        status, provider_reference, failure_reason = _simulated_send(recipient_fax_number, document_summary)
    else:
        raise NotImplementedError(f"Fax provider '{FAX_PROVIDER}' is not implemented.")

    fax = FaxLog(
        tenant_id=tenant_id,
        patient_id=patient_id,
        subject_type=subject_type,
        subject_id=subject_id,
        recipient_name=(recipient_name or "").strip() or "Unknown recipient",
        recipient_fax_number=(recipient_fax_number or "").strip(),
        status=status,
        provider=FAX_PROVIDER,
        provider_reference=provider_reference,
        document_summary=document_summary,
        failure_reason=failure_reason,
        sent_at=datetime.now(timezone.utc) if status == "SENT" else None,
        created_by=created_by,
    )
    db.add(fax)
    db.commit()
    db.refresh(fax)
    return fax
