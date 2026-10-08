from hourtime.domain.entities import TimeEntry
from hourtime.domain.errors import NotFound, ValidationError
from hourtime.interfaces.repositories import TimeEntryRepository
from hourtime.interfaces.services import Clock, UnitOfWork
from hourtime.use_cases.access import get_owned_time_entry
from hourtime.use_cases.dto import StopTimerInput
from hourtime.use_cases.time_entries.rules import END_TIME, reject_future


class StopTimer:
    def __init__(self, entries: TimeEntryRepository, clock: Clock, uow: UnitOfWork) -> None:
        self._entries = entries
        self._clock = clock
        self._uow = uow

    async def execute(self, data: StopTimerInput) -> TimeEntry:
        now = self._clock.now()

        if data.entry_id is None:
            entry = await self._entries.get_running(data.user_id)
            if entry is None:
                raise NotFound("No timer is running")
        else:
            entry = await get_owned_time_entry(
                self._entries, data.user_id, data.workspace_id, data.entry_id
            )
            if not entry.is_running:
                raise ValidationError("This entry is already stopped")

        stopped_at = data.stopped_at or now
        reject_future(stopped_at, now, END_TIME)
        stopped_at = min(stopped_at, now)
        if stopped_at <= entry.started_at:
            raise ValidationError("The end time must be later than the start time")

        stopped = await self._entries.update(entry.stop(stopped_at))
        await self._uow.commit()
        return stopped
