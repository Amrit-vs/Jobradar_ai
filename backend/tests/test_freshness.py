from datetime import datetime, timedelta, timezone

import pytest

from app.services.freshness import classify_freshness


@pytest.mark.parametrize(("age_days", "expected"), [(0, "FRESH"), (1, "FRESH"), (2, "ACTIVE"), (3, "ACTIVE"), (4, "URGENT"), (5, "URGENT"), (7, "OLDER")])
def test_freshness_thresholds(age_days: int, expected: str) -> None:
    now = datetime(2026, 9, 8, tzinfo=timezone.utc)
    assert classify_freshness(now - timedelta(days=age_days), now) == expected

