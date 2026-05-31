from __future__ import annotations

from collections import Counter


def build_loc_segments(loc_timeline: list[dict]) -> list[dict]:
    """
    Converts daily LOC timeline into claim-ready contiguous segments.

    Segment break occurs when:
    - loc changes
    - pos changes
    - facility_name changes
    """
    if not loc_timeline:
        return []

    segments: list[dict] = []

    current = {
        "start_date": loc_timeline[0]["date"],
        "end_date": loc_timeline[0]["date"],
        "loc": loc_timeline[0]["loc"],
        "pos": loc_timeline[0]["pos"],
        "facility_name": loc_timeline[0].get("facility_name"),
    }

    for row in loc_timeline[1:]:
        same_segment = (
            row["loc"] == current["loc"]
            and row["pos"] == current["pos"]
            and row.get("facility_name") == current.get("facility_name")
        )

        if same_segment:
            current["end_date"] = row["date"]
            continue

        segments.append(current)
        current = {
            "start_date": row["date"],
            "end_date": row["date"],
            "loc": row["loc"],
            "pos": row["pos"],
            "facility_name": row.get("facility_name"),
        }

    segments.append(current)
    return segments


def build_loc_summary(loc_timeline: list[dict]) -> dict:
    """
    Exact day breakdown required for export/print.

    Returns:
    {
        "routine_days": 10,
        "gip_days": 5,
        "respite_days": 0,
        "continuous_care_days": 2,
        "mixed": True
    }
    """
    counts = Counter(row["loc"] for row in loc_timeline if row["loc"])

    routine_days = counts.get("ROUTINE", 0)
    gip_days = counts.get("GIP", 0)
    respite_days = counts.get("RESPITE", 0)
    continuous_care_days = counts.get("CONTINUOUS CARE", 0)

    active_locs = sum(
        1
        for v in [routine_days, gip_days, respite_days, continuous_care_days]
        if v > 0
    )

    return {
        "routine_days": routine_days,
        "gip_days": gip_days,
        "respite_days": respite_days,
        "continuous_care_days": continuous_care_days,
        "mixed": active_locs > 1,
    }