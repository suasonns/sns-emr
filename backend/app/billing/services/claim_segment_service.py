from __future__ import annotations

from datetime import date
from decimal import Decimal


class ClaimSegmentError(RuntimeError):
    pass


def _inclusive_days(start_date: date, end_date: date) -> int:
    return (end_date - start_date).days + 1


def build_claim_lines(
    loc_segments: list[dict],
    rate_schedule: dict | None = None,
) -> list[dict]:
    """
    Converts LOC segments into claim-level billing lines.
    """

    if not loc_segments:
        return []

    claim_lines: list[dict] = []

    for segment in loc_segments:
        start_date = segment["start_date"]
        end_date = segment["end_date"]
        loc = segment["loc"]
        pos = segment["pos"]

        if not start_date or not end_date or not loc:
            continue

        days = _inclusive_days(start_date, end_date)

        # ✅ Safe default rate handling
        rate = Decimal("0.00")
        if rate_schedule and loc in rate_schedule:
            rate = Decimal(str(rate_schedule[loc]))

        amount = rate * Decimal(days)

        claim_lines.append(
            {
                "from_date": str(start_date),
                "to_date": str(end_date),
                "days": days,
                "loc": loc,
                "pos": pos,
                "facility_name": segment.get("facility_name"),
                "revenue_code": _map_revenue_code(loc),
                "rate": str(rate),
                "estimated_amount": str(amount),
            }
        )

    return claim_lines


def _map_revenue_code(loc: str) -> str | None:
    """
    Basic hospice revenue code mapping (STRUCTURE ONLY)
    """

    mapping = {
        "ROUTINE": "0651",
        "CONTINUOUS CARE": "0652",
        "RESPITE": "0655",
        "GIP": "0656",
    }

    return mapping.get(loc)
