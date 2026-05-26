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
    Enterprise-safe placeholder implementation.

    Purpose:
    - Unblocks startup (import resolution)
    - Provides deterministic behavior for /regulatory-reports/{id}/certify

    Replace later with real persistence logic:
    - Load report row
    - Check lock status
    - Set certified fields
    - Compute integrity hash
    - Commit in caller-controlled transaction if desired
    """

    # NOTE: This is a minimal deterministic object to keep runtime stable.
    # DO NOT raise internal errors; service layer can raise ReportNotFound/ReportLocked
    # once real DB models are wired.
    return RegulatoryReport(
        id=str(report_id),
        status="CERTIFIED",
        certified_at=datetime.utcnow(),
        certified_by=str(user_id),
        integrity_hash="demo_hash",
    )
