from datetime import datetime, timedelta, timezone


FRESHNESS_FRESH = "FRESH"
FRESHNESS_ACTIVE = "ACTIVE"
FRESHNESS_URGENT = "URGENT"
FRESHNESS_OLDER = "OLDER"


def classify_freshness(posted_at: datetime | None, now: datetime | None = None) -> str:
    """Return a display freshness label; no assumption is made about application closure."""
    if posted_at is None:
        return FRESHNESS_OLDER
    current = now or datetime.now(timezone.utc)
    value = posted_at if posted_at.tzinfo else posted_at.replace(tzinfo=timezone.utc)
    age = max(current - value, timedelta())
    if age <= timedelta(days=1):
        return FRESHNESS_FRESH
    if age <= timedelta(days=3):
        return FRESHNESS_ACTIVE
    if age <= timedelta(days=5):
        return FRESHNESS_URGENT
    return FRESHNESS_OLDER


def job_status_for_freshness(freshness: str) -> str:
    return "NEW" if freshness == FRESHNESS_FRESH else freshness

