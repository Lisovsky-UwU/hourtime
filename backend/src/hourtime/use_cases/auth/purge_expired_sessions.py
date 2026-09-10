from datetime import timedelta

from hourtime.interfaces.repositories import SessionRepository
from hourtime.interfaces.services import Clock, UnitOfWork


class PurgeExpiredSessions:
    """Retention: drop sessions whose refresh token died long enough ago.

    Kept as a use case rather than a cron script so the retention window is
    enforced in one place, whoever triggers it.
    """

    def __init__(
        self,
        sessions: SessionRepository,
        clock: Clock,
        uow: UnitOfWork,
        *,
        retention: timedelta,
    ) -> None:
        self._sessions = sessions
        self._clock = clock
        self._uow = uow
        self._retention = retention

    async def execute(self) -> int:
        cutoff = self._clock.now() - self._retention
        removed = await self._sessions.delete_expired_before(cutoff)
        await self._uow.commit()
        return removed
