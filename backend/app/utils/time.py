from datetime import datetime, UTC


def utc_now() -> datetime:
    """
    ✅ Single source of truth for system time
    ✅ Always timezone-aware UTC
    """
    return datetime.now(UTC)
