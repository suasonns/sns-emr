from __future__ import annotations

import math


def calculate_units(minutes: int) -> int:
    if minutes <= 0:
        return 0
    return math.ceil(minutes / 15)


def summarize_units(total_minutes: int) -> dict:
    return {
        "total_minutes": total_minutes,
        "total_units": calculate_units(total_minutes),
    }
