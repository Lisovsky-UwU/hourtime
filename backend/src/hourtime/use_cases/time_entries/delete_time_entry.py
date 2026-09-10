from uuid import UUID

from hourtime.interfaces.repositories import TimeEntryRepository
from hourtime.interfaces.services import UnitOfWork
from hourtime.use_cases.access import get_owned_time_entry


class DeleteTimeEntry:
    def __init__(self, entries: TimeEntryRepository, uow: UnitOfWork) -> None:
        self._entries = entries
        self._uow = uow

    async def execute(self, user_id: UUID, entry_id: UUID) -> None:
        entry = await get_owned_time_entry(self._entries, user_id, entry_id)
        await self._entries.delete(entry.id)
        await self._uow.commit()
