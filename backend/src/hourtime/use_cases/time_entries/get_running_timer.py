from uuid import UUID

from hourtime.domain.entities import TimeEntry
from hourtime.interfaces.repositories import TimeEntryRepository


class GetRunningTimer:
    """What the frontend asks for on load and whenever the tab regains focus."""

    def __init__(self, entries: TimeEntryRepository) -> None:
        self._entries = entries

    async def execute(self, user_id: UUID) -> TimeEntry | None:
        return await self._entries.get_running(user_id)
