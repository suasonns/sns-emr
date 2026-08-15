# backend/app/services/regulatory_report_service.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session


class ReportNotFound(Exception):
    """Raised when a regulatory report does not exist."""
    pass


class ReportLocked(Exception):
    """Raised when a regulatory report is already certified/locked."""
    pass


@dataclass
class RegulatoryReport:
    id: str
    status: str
    certified_at: Optional[datetime]
    certified_by: Optional[str]
    integrity_hash: Optional[str]


def certify_and_lock_report(
    db: Session,
    report_id,
    user_id,
) -> RegulatoryReport:
    """
    Production-safe placeholder.

    This implementation intentionally performs no
    certification, persistence, locking, audit logging,
    or integrity-hash generation.

    A future implementation should:

    - Load the report from storage
    - Validate existence
    - Validate lock state
    - Generate integrity hash
    - Record certification metadata
    - Write audit entries
    - Persist transaction

    Until then, return a non-certified object with
    no fabricated certification data.
    """

    return RegulatoryReport(
        id=str(report_id),
        status="PENDING",
        certified_at=None,
        certified_by=None,
        integrity_hash=None,
    )