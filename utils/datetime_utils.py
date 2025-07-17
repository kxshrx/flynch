from datetime import datetime, timezone
from typing import Optional


class DateTimeManager:
    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def parse_github_datetime(dt_string: str) -> datetime:
        if dt_string.endswith("Z"):
            dt_string = dt_string.replace("Z", "+00:00")
        return datetime.fromisoformat(dt_string)

    @staticmethod
    def compare_datetimes(dt1: datetime, dt2: datetime) -> int:
        dt1_utc = dt1 if dt1.tzinfo else dt1.replace(tzinfo=timezone.utc)
        dt2_utc = dt2 if dt2.tzinfo else dt2.replace(tzinfo=timezone.utc)

        if dt1_utc < dt2_utc:
            return -1
        elif dt1_utc > dt2_utc:
            return 1
        else:
            return 0
