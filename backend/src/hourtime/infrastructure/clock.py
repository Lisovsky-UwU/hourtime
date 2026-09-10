from datetime import UTC, datetime

from hourtime.interfaces.services import Clock


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(UTC)
